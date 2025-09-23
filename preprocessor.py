import json
import pandas as pd
import os
import glob
from sentence_transformers import SentenceTransformer, util
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
from sklearn.decomposition import PCA

def log_error(e, log_file):
    try:
        with open(log_file, "a") as f:
            json.dump({"error": str(e)}, f)
            f.write("\n")
    except:
        pass

def extract_columns_from_text(user_input, columns):
    lower_input = user_input.lower()
    return [col for col in columns if col.lower() in lower_input]

def drop_columns(user_input, dataset, target_column, columns, log_file):
    try:
        cols = extract_columns_from_text(user_input, columns)
        cols = [c for c in cols if c != target_column]
        if cols:
            dataset.drop(columns=cols, inplace=True)
    except Exception as e:
        log_error(e, log_file)
    return dataset

def fill_missing_mean(user_input, dataset, target_column, columns, log_file):
    try:
        cols = extract_columns_from_text(user_input, columns)
        if not cols:
            cols = dataset.select_dtypes(include="number").columns.tolist()
            if target_column in cols:
                cols.remove(target_column)
        dataset[cols] = dataset[cols].fillna(dataset[cols].mean())
    except Exception as e:
        log_error(e, log_file)
    return dataset

def fill_missing_median(user_input, dataset, target_column, columns, log_file):
    try:
        cols = extract_columns_from_text(user_input, columns)
        if not cols:
            cols = dataset.select_dtypes(include="number").columns.tolist()
            if target_column in cols:
                cols.remove(target_column)
        dataset[cols] = dataset[cols].fillna(dataset[cols].median())
    except Exception as e:
        log_error(e, log_file)
    return dataset

def fill_missing_mode(user_input, dataset, target_column, columns, log_file):
    try:
        cols = extract_columns_from_text(user_input, columns)
        if not cols:
            cols = dataset.select_dtypes(include=["object", "category", "string"]).columns.tolist()
            if target_column in cols:
                cols.remove(target_column)
        for col in cols:
            if len(dataset[col].mode()) > 0:
                dataset[col].fillna(dataset[col].mode()[0], inplace=True)
    except Exception as e:
        log_error(e, log_file)
    return dataset

def remove_duplicates(user_input, dataset, log_file):
    try:
        dataset.drop_duplicates(inplace=True)
    except Exception as e:
        log_error(e, log_file)
    return dataset

def fix_data_types(user_input, dataset, columns, log_file):
    try:
        dtype_dict = {}
        user_lower = user_input.lower()
        for col in columns:
            if f"{col} to int" in user_lower:
                dtype_dict[col] = int
            elif f"{col} to float" in user_lower:
                dtype_dict[col] = float
            elif f"{col} to str" in user_lower:
                dtype_dict[col] = str
            elif f"{col} to date" in user_lower or f"{col} to datetime" in user_lower:
                dtype_dict[col] = "datetime"

        for col, dtype in dtype_dict.items():
            if dtype == "datetime":
                dataset[col] = pd.to_datetime(dataset[col], errors="coerce")
            else:
                dataset[col] = dataset[col].astype(dtype)
    except Exception as e:
        log_error(e, log_file)
    return dataset

def standardize_columns(user_input, dataset, target_column, columns, log_file):
    try:
        cols = extract_columns_from_text(user_input, columns)
        if not cols:
            cols = dataset.select_dtypes(include="number").columns.tolist()
            if target_column in cols:
                cols.remove(target_column)
        scaler = StandardScaler()
        dataset[cols] = scaler.fit_transform(dataset[cols])
    except Exception as e:
        log_error(e, log_file)
    return dataset

def normalize_columns(user_input, dataset, target_column, columns, log_file):
    try:
        cols = extract_columns_from_text(user_input, columns)
        if not cols:
            cols = dataset.select_dtypes(include="number").columns.tolist()
            if target_column in cols:
                cols.remove(target_column)
        scaler = MinMaxScaler()
        dataset[cols] = scaler.fit_transform(dataset[cols])
    except Exception as e:
        log_error(e, log_file)
    return dataset

def encode_categorical(user_input, dataset, target_column, columns, log_file):
    try:
        cols = extract_columns_from_text(user_input, columns)
        if not cols:
            cols = dataset.select_dtypes(include=["object", "category", "string"]).columns.tolist()
            if target_column in cols:
                cols.remove(target_column)
        cols = [c for c in cols if c in dataset.columns]
        for col in cols:
            le = LabelEncoder()
            dataset[col] = le.fit_transform(dataset[col].astype(str))
    except Exception as e:
        log_error(e, log_file)
    return dataset

def reduce_dimensions(user_input, dataset, target_column, columns, log_file):
    try:
        cols = extract_columns_from_text(user_input, columns)
        numeric_cols = [col for col in cols if col in dataset.select_dtypes(include="number").columns]

        if not numeric_cols:
            numeric_cols = dataset.select_dtypes(include="number").columns.tolist()
            if target_column in numeric_cols:
                numeric_cols.remove(target_column)

        n_components = 2
        pca = PCA(n_components=n_components)
        reduced = pca.fit_transform(dataset[numeric_cols])

        for i in range(n_components):
            dataset[f"PCA_{i+1}"] = reduced[:, i]
    except Exception as e:
        log_error(e, log_file)
    return dataset

def filter_rows(user_input, dataset, log_file):
    try:
        filtered_df = dataset.query(user_input)
        dataset = filtered_df.copy()
    except Exception as e:
        log_error(e, log_file)
    return dataset

def classifier(user_input, candidate_labels, embedder, label_embs):
    input_emb = embedder.encode(user_input, convert_to_tensor=True)
    cos_scores = util.cos_sim(input_emb, label_embs)[0]
    scores = cos_scores.tolist()
    
    label_scores = list(zip(candidate_labels, scores))
    label_scores.sort(key=lambda x: x[1], reverse=True)
    
    labels_sorted, scores_sorted = zip(*label_scores)
    
    result = {
        "sequence": user_input,
        "labels": list(labels_sorted),
        "scores": list(scores_sorted)
    }
    return result

def preprocess_dataset(input_file_path="sampleinput.json", output_csv="Processed_Dataset.csv", log_file="Output.json"):
    """
    Main function to preprocess dataset based on input configuration
    """
    # Load configuration
    try:
        with open(input_file_path) as f:
            data = json.load(f)
    except Exception as e:
        log_error(e, log_file)
        return False

    dataset_path = data["path"]
    target_column = data["target"]
    threshold = 0.4

    # Load dataset
    try:
        dataset = pd.read_csv(dataset_path)
    except Exception as e:
        log_error(e, log_file)
        return False

    columns = dataset.columns.tolist()
    numprompt = len(data) - 2

    # Initialize embedder
    try:
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        log_error(e, log_file)
        return False

    # Define candidate labels
    candidate_labels = [
        "drop columns from dataset",
        "fill missing values with mean imputation",
        "fill missing values with median imputation",
        "fill missing values with mode imputation",
        "remove duplicate rows",
        "convert or change data types of columns",
        "standardize numeric columns using z-score scaling",
        "normalize numeric columns to range 0 to 1",
        "encode categorical columns using label encoding",
        "reduce dataset dimensions with PCA",
        "filter dataset rows based on conditions"
    ]

    # Pre-encode candidate labels
    label_embs = embedder.encode(candidate_labels, convert_to_tensor=True)

    # Intent function mapping
    intent_function_mapping = {
        "drop columns from dataset": lambda ui: drop_columns(ui, dataset, target_column, columns, log_file),
        "fill missing values with mean imputation": lambda ui: fill_missing_mean(ui, dataset, target_column, columns, log_file),
        "fill missing values with median imputation": lambda ui: fill_missing_median(ui, dataset, target_column, columns, log_file),
        "fill missing values with mode imputation": lambda ui: fill_missing_mode(ui, dataset, target_column, columns, log_file),
        "remove duplicate rows": lambda ui: remove_duplicates(ui, dataset, log_file),
        "convert or change data types of columns": lambda ui: fix_data_types(ui, dataset, columns, log_file),
        "standardize numeric columns using z-score scaling": lambda ui: standardize_columns(ui, dataset, target_column, columns, log_file),
        "normalize numeric columns to range 0 to 1": lambda ui: normalize_columns(ui, dataset, target_column, columns, log_file),
        "encode categorical columns using label encoding": lambda ui: encode_categorical(ui, dataset, target_column, columns, log_file),
        "reduce dataset dimensions with PCA": lambda ui: reduce_dimensions(ui, dataset, target_column, columns, log_file),
        "filter dataset rows based on conditions": lambda ui: filter_rows(ui, dataset, log_file)
    }

    # Process prompts
    for i in range(numprompt):
        user_input = data[f"prompt_{i+1}"]
        result = classifier(user_input, candidate_labels, embedder, label_embs)
        action = result['labels'][0]
        if result['scores'][0] >= threshold:
            dataset = intent_function_mapping[action](user_input)
        else:
            log_error(f"Unrecognized prompt: {user_input}", log_file)

    # Handle target column - create dummy variables
    if target_column in dataset.columns:
        try:
            target_dummies = pd.get_dummies(dataset[target_column], prefix=target_column)
            dataset.drop(columns=[target_column], inplace=True)
            dataset = pd.concat([dataset, target_dummies], axis=1)
        except Exception as e:
            log_error(e, log_file)

    # Save processed dataset
    try:
        dataset.to_csv(output_csv, index=False)
    except Exception as e:
        log_error(e, log_file)
        return False

    # Update log file with processed dataset path
    try:
        log_data = {
            "status": "success",
            "message": "Dataset preprocessing completed successfully",
            "Processed_dataset_path": output_csv,
            "original_dataset_path": dataset_path,
            "target_column": target_column,
            "final_shape": list(dataset.shape),
            "final_columns": list(dataset.columns)
        }
        
        # Check if there were any errors logged previously
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                content = f.read().strip()
                if content:
                    # Handle multiple JSON objects in file (errors)
                    lines = content.split('\n')
                    errors = []
                    for line in lines:
                        if line.strip():
                            try:
                                error_data = json.loads(line)
                                if "error" in error_data:
                                    errors.append(error_data["error"])
                            except:
                                pass
                    if errors:
                        log_data["errors"] = errors
                        log_data["status"] = "completed_with_errors"
                        log_data["message"] = f"Dataset preprocessing completed with {len(errors)} error(s)"
        
        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        # If all else fails, create a minimal output file
        try:
            with open(log_file, "w") as f:
                json.dump({
                    "status": "error", 
                    "message": f"Error updating output file: {str(e)}",
                    "Processed_dataset_path": output_csv
                }, f, indent=2)
        except:
            pass

    return True

if __name__ == "__main__":
    preprocess_dataset()