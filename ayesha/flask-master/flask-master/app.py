from flask import Flask, render_template, request, redirect, url_for
import json
import subprocess
import os
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        # For Python 3.7+
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # For older Python versions
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Support Unicode in JSON responses

# Ensure all responses use UTF-8 encoding
@app.after_request
def after_request(response):
    response.headers['Content-Type'] = response.headers.get('Content-Type', 'text/html') + '; charset=utf-8'
    return response

session_data = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat/<process_name>")
def chat(process_name):
    if process_name == "data_preprocessing":
        session_data.clear()
        session_data["steps"] = []
        session_data["conversation"] = []  # Track conversation history
    elif process_name == "data_acquisition":
        session_data.clear()
        session_data["conversation"] = []  # Add conversation for data_acquisition too
    
    return render_template("chatbot.html", process_name=process_name, stage="start", conversation=session_data.get("conversation", []))

@app.route("/submit/<process_name>", methods=["POST"])
def submit(process_name):
    global session_data
    
    # Initialize conversation if it doesn't exist
    if "conversation" not in session_data:
        session_data["conversation"] = []
    
    if process_name == "data_preprocessing":
        stage = request.form.get("stage")

        if stage == "start":
            file_path = request.form.get("csv_path")
            
            # Clean and normalize the file path
            file_path = file_path.strip()  # Remove leading/trailing spaces
            
            # Remove surrounding quotes if present
            if (file_path.startswith('"') and file_path.endswith('"')) or (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
            
            # Normalize the path to use proper backslashes for Windows
            file_path = os.path.normpath(file_path)
            
            session_data["file_path"] = file_path
            session_data["conversation"].append({"type": "user", "message": file_path})
            session_data["conversation"].append({"type": "bot", "message": f"Great! File path received: {file_path}. Now, please provide the target column name."})
            return render_template("chatbot.html",
                                   process_name=process_name,
                                   stage="target_column",
                                   filepath=file_path,
                                   conversation=session_data["conversation"])

        elif stage == "target_column":
            target_column = request.form.get("target_column")
            session_data["target_column"] = target_column
            session_data["conversation"].append({"type": "user", "message": target_column})
            session_data["conversation"].append({"type": "bot", "message": f"Target column set: {target_column}. Now let's add preprocessing steps. Type 'END' when finished."})
            return render_template("chatbot.html",
                                   process_name=process_name,
                                   stage="preprocessing_steps",
                                   target_column=target_column,
                                   conversation=session_data["conversation"])

        elif stage == "preprocessing_steps":
            step = request.form.get("preprocess_step").strip()
            if step.lower() not in ["no", "end", "done"]:
                session_data["steps"].append(step)
                session_data["conversation"].append({"type": "user", "message": step})
                session_data["conversation"].append({"type": "bot", "message": f"Step added: {step}. Add more steps or type 'END' to finish."})
                return render_template("chatbot.html",
                                       process_name=process_name,
                                       stage="preprocessing_steps",
                                       last_step=step,
                                       conversation=session_data["conversation"])
            else:
                # User wants to finish - save JSON and process
                session_data["conversation"].append({"type": "user", "message": step.upper()})
                
                # Create the JSON file in your desired format
                preprocessing_data = {
                    "path": session_data.get("file_path"),
                    "target": session_data.get("target_column")
                }
                
                # Add prompts in the format prompt_1, prompt_2, etc.
                for i, prompt in enumerate(session_data.get("steps", []), 1):
                    preprocessing_data[f"prompt_{i}"] = prompt
                
                # Save JSON file in the main project directory (same level as preprocessor.py)
                json_filename = "sampleinput.json"
                main_project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                json_full_path = os.path.join(main_project_dir, json_filename)
                
                with open(json_full_path, 'w') as f:
                    json.dump(preprocessing_data, f, indent=4)
                
                # Call the actual preprocessor.py
                try:
                    # Change to the main project directory where preprocessor.py is located
                    preprocessor_path = os.path.join(main_project_dir, "preprocessor.py")
                    
                    # Use the Dataset conda environment Python
                    dataset_python = r"D:\anaconda\envs\Dataset\python.exe"
                    
                    # Run the preprocessor with the correct Python environment
                    result = subprocess.run(
                        [dataset_python, preprocessor_path],
                        cwd=main_project_dir,
                        capture_output=True,
                        text=True,
                        timeout=6600  # 5 minute timeout
                    )
                    
                    # Check if Output.json was created
                    output_json_path = os.path.join(main_project_dir, "Output.json")
                    
                    if os.path.exists(output_json_path):
                        # Read the Output.json file
                        with open(output_json_path, 'r') as f:
                            output_data = json.load(f)
                        
                        # Extract values from output JSON
                        status = output_data.get("status", "unknown")
                        processed_dataset_path = output_data.get("Processed_dataset_path", "")
                        final_shape = output_data.get("final_shape", [])
                        shape_str = f"{tuple(final_shape)}" if final_shape else "Unknown"

                        if status == "success":
                            backend_output = {
                                "status": "success",
                                "message": f"[OK] Preprocessing completed!\n[FILE] Saved at: {processed_dataset_path}\n[DATA] Final shape: {shape_str}",
                                "processed_dataset_path": processed_dataset_path,
                                "final_shape": shape_str
                            }
                        elif status == "completed_with_errors":
                            backend_output = {
                                "status": "warning",
                                "message": f"[!] Completed with errors: {', '.join(output_data.get('errors', []))}"[:200],
                                "processed_dataset_path": processed_dataset_path,
                                "final_shape": shape_str
                            }
                        else:
                            backend_output = {
                                "status": "error",
                                "message": output_data.get("message", "Unknown error occurred")
                            }
                    else:
                        # No Output.json found
                        backend_output = {
                            "status": "error",
                            "message": f"[X] Preprocessing failed - no Output.json created.\nError: {result.stderr[:200] if result.stderr else 'Unknown error'}"
                        }
                        
                except subprocess.TimeoutExpired:
                    backend_output = {
                        "status": "error",
                        "message": "Preprocessing timed out (exceeded 5 minutes)"
                    }
                except Exception as e:
                    backend_output = {
                        "status": "error", 
                        "message": f"Error running preprocessor: {str(e)}"
                    }

                session_data["conversation"].append({"type": "bot", "message": backend_output.get("message", "Processing complete.")})
                
                return render_template("chatbot.html",
                                       process_name=process_name,
                                       stage="finished",
                                       backend_output=backend_output,  # Pass dictionary directly, not JSON string
                                       conversation=session_data["conversation"])

    elif process_name == "data_acquisition":
        action = request.form.get("action", "")  # "create" or "search"
        user_input = request.form.get("user_input", "").strip()

        # Add user input to conversation
        session_data["conversation"].append({"type": "user", "message": user_input})

        main_project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        
        if action == "create":
            # Call simulator_main.py to generate dataset
            try:
                simulator_path = os.path.join(main_project_dir, "simulator_main.py")
                
                # Parse input: domain, columns (optional), rows
                # Expected format: "domain | columns | rows" or "domain | rows"
                parts = [p.strip() for p in user_input.split("|")]
                
                if len(parts) == 2:
                    domain, total_rows = parts[0], parts[1]
                    columns = ""
                elif len(parts) == 3:
                    domain, columns, total_rows = parts[0], parts[1], parts[2]
                else:
                    domain = user_input
                    columns = ""
                    total_rows = "100"
                
                # Prepare input for simulator
                simulator_input = f"{domain}\nno\n{columns}\n{total_rows}\n"
                
                session_data["conversation"].append({"type": "bot", "message": f"Generating dataset for domain: {domain}... Please wait..."})
                
                result = subprocess.run(
                    [sys.executable, simulator_path],
                    input=simulator_input,
                    cwd=main_project_dir,
                    capture_output=True,
                    text=True,
                    timeout=6600
                )
                
                output = result.stdout + result.stderr
                
                # Parse output to find generated file
                import re
                file_match = re.search(r"saved as '([^']+)'", output)
                
                if file_match:
                    csv_file = file_match.group(1)
                    row_match = re.search(r"with (\d+) rows", output)
                    rows_generated = row_match.group(1) if row_match else "Unknown"
                    
                    backend_output = {
                        "status": "success",
                        "message": f"Dataset generated successfully with {rows_generated} rows!",
                        "file_path": csv_file,
                        "domain": domain,
                        "rows": rows_generated,
                        "output": output
                    }
                    session_data["conversation"].append({"type": "bot", "message": f"[OK] Dataset generated successfully! File saved at: {csv_file}"})
                else:
                    backend_output = {"status": "error", "message": "Generation failed", "output": output}
                    session_data["conversation"].append({"type": "bot", "message": "[X] Dataset generation failed. Check output for details."})
                    
            except subprocess.TimeoutExpired:
                backend_output = {"status": "error", "message": "Generation timeout (exceeded 5 minutes)"}
                session_data["conversation"].append({"type": "bot", "message": "[X] Generation timeout. Please try again."})
            except Exception as e:
                backend_output = {"status": "error", "message": f"Error: {str(e)}"}
                session_data["conversation"].append({"type": "bot", "message": f"[X] Error: {str(e)}"})
        
        elif action == "search":
            # Call searcher_main.py to find datasets
            try:
                searcher_path = os.path.join(main_project_dir, "searcher_main.py")
                
                # Prepare input for searcher
                searcher_input = f"{user_input}\n\n"
                
                session_data["conversation"].append({"type": "bot", "message": f"Searching for datasets matching: '{user_input}'... This may take several minutes..."})
                
                result = subprocess.run(
                    [sys.executable, searcher_path],
                    input=searcher_input,
                    cwd=main_project_dir,
                    capture_output=True,
                    text=True,
                    timeout=6600
                )
                
                output = result.stdout + result.stderr
                
                # Look for saved results JSON file
                results_folder = os.path.join(main_project_dir, "results")
                if os.path.exists(results_folder):
                    json_files = [f for f in os.listdir(results_folder) if f.startswith("ml_datasets_") and f.endswith(".json")]
                    if json_files:
                        latest_file = max([os.path.join(results_folder, f) for f in json_files], key=os.path.getmtime)
                        
                        with open(latest_file, 'r') as f:
                            search_results = json.load(f)
                        
                        datasets = search_results.get("datasets", [])[:5]
                        
                        backend_output = {
                            "status": "success",
                            "message": f"Found {search_results.get('total_found', 0)} datasets. Showing top 5.",
                            "query": user_input,
                            "total_found": search_results.get("total_found", 0),
                            "datasets": datasets,
                            "output": output
                        }
                        session_data["conversation"].append({"type": "bot", "message": f"[OK] Found {len(datasets)} relevant datasets! Check results below."})
                    else:
                        backend_output = {"status": "error", "message": "No results found", "output": output}
                        session_data["conversation"].append({"type": "bot", "message": "[X] No datasets found."})
                else:
                    backend_output = {"status": "error", "message": "Results folder not found", "output": output}
                    session_data["conversation"].append({"type": "bot", "message": "[X] Results folder not found."})
                    
            except subprocess.TimeoutExpired:
                backend_output = {"status": "error", "message": "Search timeout (exceeded 10 minutes)"}
                session_data["conversation"].append({"type": "bot", "message": "[X] Search timeout. Please try again."})
            except Exception as e:
                backend_output = {"status": "error", "message": f"Error: {str(e)}"}
                session_data["conversation"].append({"type": "bot", "message": f"[X] Error: {str(e)}"})
        
        else:
            backend_output = {"status": "error", "message": "Invalid action"}
            session_data["conversation"].append({"type": "bot", "message": "[X] Please use Create or Search button."})

        return render_template("chatbot.html",
                               process_name=process_name,
                               stage="finished",
                               backend_output=backend_output,
                               conversation=session_data.get("conversation", []))

    else:
        return "Unknown process", 400

if __name__ == "__main__":
    # Ensure UTF-8 output on Windows
    if sys.platform == 'win32':
        os.system('chcp 65001 >nul')  # Set console to UTF-8
    app.run(debug=True)
