import os
import csv
import pandas as pd
from io import StringIO
from openai import OpenAI

# === Configure OpenRouter API ===
OPENROUTER_API_KEY = "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"

if not OPENROUTER_API_KEY:
    raise EnvironmentError("OPENROUTER_API_KEY environment variable not set.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

MODEL = "google/gemma-3n-e4b-it:free"

# === Helper functions ===
def clean_csv_text(text: str) -> str:
    """Remove markdown and unnecessary text."""
    text = text.replace("```csv", "").replace("```", "")
    return text.strip()

def extract_columns_from_csv(csv_text: str):
    """Extract header row from CSV text."""
    lines = clean_csv_text(csv_text).splitlines()
    if not lines:
        return []
    return [c.strip() for c in lines[0].split(",")]

def ask_llm_for_columns(domain: str):
    """Ask LLM to suggest dataset column names for the given domain."""
    prompt = (
        f"You are an expert data scientist specializing in dataset design.\n\n"
        f"Task: Suggest between 5 and 8 well-structured column names for a dataset related to '{domain}'.\n"
        f"These column names should represent realistic and diverse attributes relevant to that field.\n\n"
        f"Return ONLY a single comma-separated list of column names — no markdown, no text, no explanations."
    )
    print("\n🤖 Asking LLM to decide column names...\n")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    cols_text = response.choices[0].message.content.strip()
    return [c.strip() for c in cols_text.split(",") if c.strip()]

def parse_csv_to_df(csv_text):
    """Convert clean CSV text to pandas DataFrame."""
    cleaned = clean_csv_text(csv_text)
    try:
        df = pd.read_csv(StringIO(cleaned))
    except Exception:
        # handle missing headers or malformed CSV
        lines = cleaned.splitlines()
        if len(lines) < 2:
            return pd.DataFrame()
        header = [c.strip() for c in lines[0].split(",")]
        data = [r.split(",") for r in lines[1:]]
        df = pd.DataFrame(data, columns=header)
    return df.dropna(how="all").reset_index(drop=True)

# === Core dataset generator ===
def generate_dataset(domain, columns, total_rows=100):
    """Generate dataset in consistent 50-row batches using DataFrames until row target is met."""
    batch_size = 50
    combined_df = pd.DataFrame()
    batch_count = 0

    print(f"\n🧠 Generating dataset for '{domain}' until {total_rows} rows are collected...\n")

    while len(combined_df) < total_rows:
        batch_count += 1
        rows_needed = total_rows - len(combined_df)
        rows_in_batch = min(batch_size, rows_needed)

        # First batch gets full structure and header
        if batch_count == 1:
            prompt = (
                f"You are a professional data generator. Create a realistic tabular dataset about '{domain}'.\n\n"
                f"⚙️ Requirements:\n"
                f"- Generate exactly {rows_in_batch} rows of data.\n"
                f"- The dataset must strictly have these columns, in this exact order: {', '.join(columns)}.\n"
                f"- Each row should contain realistic, diverse, and consistent values matching the meaning of each column.\n"
                f"- Output ONLY valid CSV format with one header line followed by the rows.\n"
                f"- Do NOT include markdown, explanations, or commentary.\n"
                f"- Ensure that values vary naturally (e.g., if dates, use valid ranges; if money, vary the amounts).\n\n"
                f"🎯 Your output must begin with the header row and then the data rows, nothing else."
            )
        else:
            prompt = (
                f"Continue generating more unique data for the domain '{domain}'.\n\n"
                f"⚙️ Requirements:\n"
                f"- Generate exactly {rows_in_batch} new rows following the same structure.\n"
                f"- Use exactly these columns in this order: {', '.join(columns)}.\n"
                f"- Do NOT include any header, explanation, or markdown.\n"
                f"- Ensure consistency in data format and column alignment.\n"
                f"- Every row must contain valid and correctly formatted data.\n\n"
                f"🎯 Output ONLY CSV rows — no text or markdown."
            )

        print(f"🔹 Generating batch {batch_count} ({rows_in_batch} rows)...")

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
            )

            data_text = response.choices[0].message.content.strip()
            df_batch = parse_csv_to_df(data_text)

            if df_batch.empty:
                print(f"⚠️ Empty batch {batch_count}, retrying...")
                continue

            # Drop duplicate headers if repeated
            if list(df_batch.columns.str.lower()) == [c.lower() for c in columns]:
                pass
            else:
                df_batch.columns = columns  # ensure consistency

            # Merge into main dataset
            combined_df = pd.concat([combined_df, df_batch], ignore_index=True)
            print(f"✅ Batch {batch_count} added — total rows so far: {len(combined_df)}")

        except Exception as e:
            print(f"❌ Error generating batch {batch_count}: {e}")
            continue

    # Trim if slightly over target
    combined_df = combined_df.iloc[:total_rows]

    # Save only once after all rows are collected
    filename = f"datasets/{domain.lower().replace(' ', '_')}_dataset.csv"
    combined_df.to_csv(filename, index=False, encoding="utf-8")
    print(f"\n✅ Final dataset saved as '{filename}' with {len(combined_df)} rows.")

# === Run from console ===
if __name__ == "__main__":
    print("=== 🧩 Universal Dataset Generator (OpenRouter LLM – Batch Merging with Pandas) ===\n")

    domain = input("Enter the domain (e.g., Finance, Healthcare, Sports): ").strip()
    col_mode = input("Do you want the LLM to decide columns? (yes/no): ").strip().lower()

    if col_mode in ["yes", "y"]:
        columns = ask_llm_for_columns(domain)
    else:
        col_input = input("Enter comma-separated columns (or leave blank to let LLM decide): ").strip()
        if col_input:
            columns = [c.strip() for c in col_input.split(",") if c.strip()]
        else:
            columns = ask_llm_for_columns(domain)

    total_rows = input("Enter total number of rows (default 100): ").strip()
    total_rows = int(total_rows) if total_rows.isdigit() else 100

    generate_dataset(domain, columns, total_rows)

    input("\nPress Enter to exit...")
