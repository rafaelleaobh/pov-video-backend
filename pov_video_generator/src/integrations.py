import requests
import time
import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText

# Placeholder functions for API interactions
# Replace with actual API calls and error handling

def generate_prompt_with_gpt4(scene_description, api_key):
    """Generates a detailed prompt using OpenAI GPT-4."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4", # Or use "gpt-3.5-turbo" if gpt-4 access is an issue
        "messages": [
            {"role": "system", "content": "You are an assistant that generates detailed, vivid, and creative prompts for an image generation model. The user will provide a simple scene description, and you should expand it into a rich prompt suitable for creating a POV (Point of View) image. Focus on visual details, atmosphere, and emotion. The output should be only the prompt itself."},
            {"role": "user", "content": scene_description}
        ],
        "max_tokens": 300
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as http_err:
        # Try to get more details from the response body if available
        error_details = http_err.response.text
        return {"error": f"OpenAI API request failed with HTTPError: {str(http_err)} - Details: {error_details}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"OpenAI API request failed: {str(e)}"}
    except (KeyError, IndexError) as e:
        return {"error": f"Failed to parse OpenAI API response: {str(e)}"}

def generate_image_with_flux(prompt, api_key):
    """Generates an image using HuggingFace FLUX model (placeholder)."""
    if not api_key:
        print("HuggingFace API key not provided for FLUX, proceeding with placeholder.")
    print(f"Simulating FLUX image generation for prompt: {prompt[:50]}...")
    # Using a more relevant placeholder or a service like Pexels for variety
    return "https://images.pexels.com/photos/356056/pexels-photo-356056.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1" # Placeholder image of a futuristic scene

def create_video_with_runway(image_url_param, prompt, api_key):
    """Initiates video generation with RunwayML using an image and returns a task ID."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # Corrected parameter name from image_prompt to image_url
    data = {
        "image_url": image_url_param, # Changed from image_prompt
        "text_prompt": prompt,
        # Add other parameters if needed by RunwayML Gen-2, e.g., motion, seed
    }
    try:
        response = requests.post("https://api.runwayml.com/v1/tasks", headers=headers, json=data, timeout=30)
        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
        # Assuming the task ID is directly in 'uuid' or similar based on typical API responses
        # If the structure is different, this needs adjustment.
        response_data = response.json()
        task_id = response_data.get("uuid") or response_data.get("task_id") # Common keys for task ID
        if not task_id:
            # Log the full response if task_id is not found as expected
            return {"error": f"RunwayML API did not return a task ID. Full response: {json.dumps(response_data)}"}
        return {"uuid": task_id} # Return as a dict to match expected structure in main.py
    except requests.exceptions.HTTPError as http_err:
        error_details = "No additional details in response."
        try:
            error_details = http_err.response.json() # Try to parse JSON error response
        except json.JSONDecodeError:
            error_details = http_err.response.text # Fallback to text if not JSON
        return {"error": f"RunwayML API request failed with HTTPError: {str(http_err)} - Details: {json.dumps(error_details) if isinstance(error_details, dict) else error_details}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"RunwayML API request failed: {str(e)}"}
    except KeyError as e:
        # This might happen if response.json() doesn't have expected keys even on success (less likely for task creation)
        return {"error": f"Failed to parse RunwayML API response for task creation: {str(e)} - Response: {response.text}"}

def check_runway_video_status(task_id, api_key):
    """Checks the status of a video generation task on RunwayML."""
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get(f"https://api.runwayml.com/v1/tasks/{task_id}", headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        error_details = "No additional details in response."
        try:
            error_details = http_err.response.json()
        except json.JSONDecodeError:
            error_details = http_err.response.text
        return {"error": f"RunwayML API status check failed with HTTPError: {str(http_err)} - Details: {json.dumps(error_details) if isinstance(error_details, dict) else error_details}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"RunwayML API status check failed: {str(e)}"}
    except KeyError as e:
        return {"error": f"Failed to parse RunwayML API status response: {str(e)} - Response: {response.text}"}

def add_to_google_sheet(spreadsheet_id, range_name, values):
    """Adds a new row to a Google Sheet. Relies on GOOGLE_APPLICATION_CREDENTIALS env var."""
    try:
        google_creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not google_creds_path:
            return {"error": "GOOGLE_APPLICATION_CREDENTIALS environment variable not set."}
        
        creds = Credentials.from_service_account_file(
            google_creds_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        service = build("sheets", "v4", credentials=creds)

        body = {
            "values": [values]
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption="USER_ENTERED", body=body).execute()
        return result
    except FileNotFoundError:
        return {"error": f"Google credentials file not found at {google_creds_path}. Check GOOGLE_APPLICATION_CREDENTIALS."}
    except Exception as e:
        return {"error": f"Google Sheets API error: {str(e)}"}

def send_email_with_gmail(recipient_email, subject, body_text):
    """Sends an email using Gmail API. Relies on GOOGLE_APPLICATION_CREDENTIALS env var."""
    try:
        google_creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not google_creds_path:
            return {"error": "GOOGLE_APPLICATION_CREDENTIALS environment variable not set."}

        creds = Credentials.from_service_account_file(
            google_creds_path, scopes=["https://www.googleapis.com/auth/gmail.send"])
        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(body_text)
        message["to"] = recipient_email
        message["subject"] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": raw_message}
        
        send_message_response = service.users().messages().send(userId="me", body=body).execute()
        return send_message_response
    except FileNotFoundError:
        return {"error": f"Google credentials file not found at {google_creds_path}. Check GOOGLE_APPLICATION_CREDENTIALS."}
    except Exception as e:
        return {"error": f"Gmail API error: {str(e)}"}

print("Integration functions are defined. Run main.py to start the Flask server.")

