import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS
import threading
import time
import json # Ensure json is imported for error details

from src.integrations import (
    generate_prompt_with_gpt4,
    generate_image_with_flux,
    create_video_with_runway,
    check_runway_video_status,
    add_to_google_sheet,
    send_email_with_gmail
)
from src.credentials_manager import get_credentials, save_credentials

app = Flask(__name__)

# Configuração do CORS para permitir a origem específica do frontend
# e as origens padrão para desenvolvimento local, se necessário.
# Esta configuração DEVE estar ativa no Render para resolver os erros de CORS.
CORS(app, resources={r"/api/*": {"origins": [
    "https://pov-video-frontend.vercel.app",
    "http://localhost:5173", 
    "http://localhost:5174"
]}})

tasks = {}
task_id_counter = 0

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route("/api/credentials", methods=["GET", "POST"])
def manage_credentials():
    if request.method == "GET":
        creds = get_credentials()
        creds["google_application_credentials_set"] = bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
        return jsonify(creds)
    elif request.method == "POST":
        data = request.get_json()
        save_credentials(data) 
        return jsonify({"message": "Credentials are managed by environment variables in production."})

def run_pov_workflow(task_id, scene_description):
    tasks[task_id]["status"] = "processing"
    tasks[task_id]["steps"].append({"name": "Starting workflow", "status": "completed", "timestamp": time.time()})

    try:
        credentials = get_credentials()
        openai_api_key = credentials.get("openai")
        huggingface_api_key = credentials.get("huggingface")
        runway_api_key = credentials.get("runwayml")
        google_spreadsheet_id = credentials.get("google_spreadsheet_id")
        gmail_recipient = credentials.get("gmail_recipient")

        if not all([openai_api_key, runway_api_key]):
            error_msg = "Missing API credentials for OpenAI or RunwayML."
            tasks[task_id]["status"] = "error"
            tasks[task_id]["error"] = error_msg
            tasks[task_id]["steps"].append({"name": "Credential Check", "status": "error", "message": error_msg, "timestamp": time.time()})
            return

        # 1. Generate Prompt with GPT-4
        tasks[task_id]["steps"].append({"name": "GPT-4 Prompt Generation", "status": "processing", "timestamp": time.time()})
        detailed_prompt = generate_prompt_with_gpt4(scene_description, openai_api_key)
        if isinstance(detailed_prompt, dict) and "error" in detailed_prompt:
            raise Exception(f"GPT-4 Error: {detailed_prompt['error']}")
        tasks[task_id]["steps"][-1]["status"] = "completed"
        tasks[task_id]["steps"][-1]["output"] = detailed_prompt
        tasks[task_id]["prompt"] = detailed_prompt

        # 2. Generate Image with HuggingFace FLUX
        tasks[task_id]["steps"].append({"name": "FLUX Image Generation", "status": "processing", "timestamp": time.time()})
        image_url = generate_image_with_flux(detailed_prompt, huggingface_api_key)
        if isinstance(image_url, dict) and "error" in image_url:
            raise Exception(f"FLUX Image Generation Error: {image_url['error']}")
        tasks[task_id]["steps"][-1]["status"] = "completed"
        tasks[task_id]["steps"][-1]["output"] = image_url
        tasks[task_id]["image_url"] = image_url

        # 3. Create Video with RunwayML
        tasks[task_id]["steps"].append({"name": "RunwayML Video Generation", "status": "processing", "timestamp": time.time()})
        runway_task_obj = create_video_with_runway(image_url, detailed_prompt, runway_api_key)
        if isinstance(runway_task_obj, dict) and "error" in runway_task_obj:
            # The error from create_video_with_runway should now be more detailed
            raise Exception(f"RunwayML Video Creation Error: {runway_task_obj['error']}")
        runway_task_id = runway_task_obj.get("uuid")
        if not runway_task_id:
             raise Exception(f"RunwayML Video Creation did not return a task ID. Response: {json.dumps(runway_task_obj)}")
        tasks[task_id]["steps"][-1]["status"] = "submitted"
        tasks[task_id]["steps"][-1]["runway_task_id"] = runway_task_id

        # 4. Check RunwayML Video Status (Polling)
        video_url = None
        max_retries = 30 # Approx 5 minutes (30 * 10 seconds)
        retry_count = 0
        tasks[task_id]["steps"].append({"name": "RunwayML Video Processing", "status": "polling", "timestamp": time.time()})
        while retry_count < max_retries:
            status_response = check_runway_video_status(runway_task_id, runway_api_key)
            if isinstance(status_response, dict) and "error" in status_response:
                # The error from check_runway_video_status should now be more detailed
                raise Exception(f"RunwayML Status Check Error: {status_response['error']}")

            current_runway_status = status_response.get("status")
            tasks[task_id]["steps"][-1]["current_runway_status"] = current_runway_status # Log current status

            if current_runway_status == "succeeded":
                video_url = status_response.get("outputs", [{}])[0].get("video") # Adjusted based on typical RunwayML Gen-2 response
                if not video_url:
                    video_url = status_response.get("url") # Fallback for older or different formats
                if not video_url:
                    raw_output = status_response.get("output") # Another fallback
                    if isinstance(raw_output, str) and raw_output.startswith("http"):
                        video_url = raw_output
                
                if video_url:
                    tasks[task_id]["steps"][-1]["status"] = "completed"
                    tasks[task_id]["steps"][-1]["output"] = video_url
                    break
                else:
                    # If status is succeeded but no URL, log the response for debugging
                    raise Exception(f"RunwayML Succeeded but no video URL found. Response: {json.dumps(status_response)}")
            elif current_runway_status == "failed":
                error_message = status_response.get('error_message', status_response.get('error', 'Unknown RunwayML error'))
                raise Exception(f"RunwayML Video Generation Failed: {error_message} - Full Response: {json.dumps(status_response)}")

            time.sleep(10)
            retry_count += 1
        else: # Loop finished without break (timeout)
            raise Exception("RunwayML video generation timed out after polling.")
        tasks[task_id]["video_url"] = video_url

        # 5. Add to Google Sheets
        if google_spreadsheet_id and os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            tasks[task_id]["steps"].append({"name": "Google Sheets Update", "status": "processing", "timestamp": time.time()})
            sheet_response = add_to_google_sheet(
                google_spreadsheet_id,
                "Sheet1",
                [scene_description, detailed_prompt, image_url, video_url, "Completed", time.ctime()]
            )
            if isinstance(sheet_response, dict) and "error" in sheet_response:
                tasks[task_id]["steps"][-1]["status"] = "warning"
                tasks[task_id]["steps"][-1]["message"] = f"Google Sheets Error: {sheet_response['error']}"
            else:
                tasks[task_id]["steps"][-1]["status"] = "completed"

        # 6. Send Email with Gmail
        if gmail_recipient and os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            tasks[task_id]["steps"].append({"name": "Gmail Notification", "status": "processing", "timestamp": time.time()})
            email_subject = f"POV Video Generated: {scene_description[:30]}..."
            email_body = f"Your POV video for the scene '{scene_description}' has been generated.\n\nPrompt: {detailed_prompt}\nImage URL: {image_url}\nVideo URL: {video_url}"
            email_response = send_email_with_gmail(
                gmail_recipient,
                email_subject,
                email_body
            )
            if isinstance(email_response, dict) and "error" in email_response:
                tasks[task_id]["steps"][-1]["status"] = "warning"
                tasks[task_id]["steps"][-1]["message"] = f"Gmail Error: {email_response['error']}"
            else:
                tasks[task_id]["steps"][-1]["status"] = "completed"

        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = video_url
        tasks[task_id]["steps"].append({"name": "Workflow Finished", "status": "completed", "timestamp": time.time()})

    except Exception as e:
        error_str = str(e)
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = error_str
        # Ensure the last processing/polling step is marked as error
        current_step_index = -1
        if tasks[task_id]["steps"]:
            if tasks[task_id]["steps"][current_step_index]["status"] in ["processing", "polling", "submitted"]:
                tasks[task_id]["steps"][current_step_index]["status"] = "error"
                tasks[task_id]["steps"][current_step_index]["message"] = error_str
            else: # If last step was already completed or errored, add a new error step
                 tasks[task_id]["steps"].append({"name": "Workflow Error", "status": "error", "message": error_str, "timestamp": time.time()})
        else: # No steps initiated yet
            tasks[task_id]["steps"].append({"name": "Workflow Initialization Error", "status": "error", "message": error_str, "timestamp": time.time()})

@app.route("/api/generate-pov", methods=["POST"])
def generate_pov_endpoint():
    global task_id_counter
    data = request.get_json()
    scene_description = data.get("scene_description")

    if not scene_description:
        return jsonify({"error": "Scene description is required"}), 400

    task_id = task_id_counter
    task_id_counter += 1
    tasks[task_id] = {"id": task_id, "status": "pending", "description": scene_description, "result": None, "error": None, "steps": []}

    thread = threading.Thread(target=run_pov_workflow, args=(task_id, scene_description))
    thread.start()

    return jsonify({"message": "POV generation started", "task_id": task_id}), 202

@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task_status(task_id):
    task = tasks.get(task_id)
    if task:
        return jsonify(task)
    return jsonify({"error": "Task not found"}), 404

@app.route("/api/tasks", methods=["GET"])
def get_all_tasks():
    return jsonify(list(tasks.values())) # Return a list of tasks for easier frontend iteration

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)

