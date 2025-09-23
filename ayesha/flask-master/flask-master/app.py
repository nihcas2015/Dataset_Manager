from flask import Flask, render_template, request
import json
import subprocess
import os
import sys

app = Flask(__name__)

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
    return render_template("chatbot.html", process_name=process_name, stage="start", conversation=session_data.get("conversation", []))

@app.route("/submit/<process_name>", methods=["POST"])
def submit(process_name):
    global session_data
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
                json_filepath = os.path.join("..", "..", "..", json_filename)  # Go back to main project directory
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
                        timeout=300  # 5 minute timeout
                    )
                    
                    # Check if Output.json was created
                    output_json_path = os.path.join(main_project_dir, "Output.json")
                    
                    if os.path.exists(output_json_path):
                        # Read the Output.json file
                        with open(output_json_path, 'r') as f:
                            output_data = json.load(f)
                        
                        # Check if there's a processed dataset path
                        processed_dataset_path = output_data.get("Processed_dataset_path", "")
                        
                        if processed_dataset_path and os.path.exists(os.path.join(main_project_dir, processed_dataset_path)):
                            backend_output = {
                                "status": "success",
                                "message": "Dataset preprocessing completed successfully!",
                                "input_json_file": json_filename,
                                "output_json_file": "Output.json",
                                "processed_dataset_path": processed_dataset_path,
                                "input_data": preprocessing_data,
                                "output_data": output_data,
                                "steps_processed": len(session_data.get("steps", [])),
                                "preprocessor_stdout": result.stdout if result.stdout else "No output",
                                "preprocessor_stderr": result.stderr if result.stderr else "No errors"
                            }
                        else:
                            backend_output = {
                                "status": "warning",
                                "message": "Preprocessing completed but no processed dataset found",
                                "input_json_file": json_filename,
                                "output_json_file": "Output.json",
                                "input_data": preprocessing_data,
                                "output_data": output_data,
                                "preprocessor_stdout": result.stdout if result.stdout else "No output",
                                "preprocessor_stderr": result.stderr if result.stderr else "No errors"
                            }
                    else:
                        # No Output.json found, check for errors
                        backend_output = {
                            "status": "error",
                            "message": "Preprocessing failed - No Output.json file created",
                            "input_json_file": json_filename,
                            "input_data": preprocessing_data,
                            "preprocessor_stdout": result.stdout if result.stdout else "No output",
                            "preprocessor_stderr": result.stderr if result.stderr else "No errors",
                            "return_code": result.returncode
                        }
                        
                except subprocess.TimeoutExpired:
                    backend_output = {
                        "status": "error",
                        "message": "Preprocessing timed out (exceeded 5 minutes)",
                        "input_json_file": json_filename,
                        "input_data": preprocessing_data
                    }
                except Exception as e:
                    backend_output = {
                        "status": "error", 
                        "message": f"Error running preprocessor: {str(e)}",
                        "input_json_file": json_filename,
                        "input_data": preprocessing_data
                    }

                session_data["conversation"].append({"type": "bot", "message": "Processing completed! JSON file created and dataset processed."})
                
                return render_template("chatbot.html",
                                       process_name=process_name,
                                       stage="finished",
                                       backend_output=json.dumps(backend_output, indent=4),
                                       conversation=session_data["conversation"])

    elif process_name == "data_acquisition":
        user_input = request.form.get("user_input", "")

        # Call acquisition backend (sample JSON)
        try:
            backend_input = {"request": user_input}
            result = subprocess.run(
                ["python", "dummy_backend_acquisition.py"],
                input=json.dumps(backend_input),
                text=True,
                capture_output=True,
                check=True
            )
            backend_output = json.loads(result.stdout)
        except:
            backend_output = {"status": "error", "message": "Backend error"}

        return render_template("chatbot.html",
                               process_name=process_name,
                               stage="finished",
                               backend_output=json.dumps(backend_output, indent=4),
                               sample_data=backend_output.get("sample_data"))

    else:
        return "Unknown process", 400

if __name__ == "__main__":
    app.run(debug=True)
