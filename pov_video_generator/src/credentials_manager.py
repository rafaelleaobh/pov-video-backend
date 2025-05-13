import os
import json

# CREDENTIALS_FILE = "credentials.json" # No longer using a file for reading in production

def get_credentials():
    creds = {
        "openai": os.environ.get("OPENAI_API_KEY"),
        "huggingface": os.environ.get("HUGGINGFACE_API_KEY"),
        "runwayml": os.environ.get("RUNWAYML_API_KEY"),
        "google_spreadsheet_id": os.environ.get("GOOGLE_SPREADSHEET_ID"),
        "gmail_recipient": os.environ.get("GMAIL_RECIPIENT"),
        # For Google JSON, its content will be read from GOOGLE_CREDENTIALS_JSON_CONTENT
        # and handled directly in main.py or integrations.py
    }
    # Remove keys with None values to avoid issues if some are not set
    return {k: v for k, v in creds.items() if v is not None}

def save_credentials(credentials_data):
    # This function is primarily for local development if a credentials.json is used.
    # In a deployed PaaS environment, credentials should be managed via the platform's env var settings.
    # Writing to a local file here will not affect the deployed application's environment variables.
    local_credentials_file = "credentials.json" # Define a local path if needed for dev
    if os.environ.get("FLASK_ENV") == "development": # Only write if in development
        try:
            with open(local_credentials_file, "w") as f:
                json.dump(credentials_data, f, indent=4)
            print(f"Credentials saved locally to {local_credentials_file} for development. This will not affect the deployed application.")
        except Exception as e:
            print(f"Error saving credentials locally: {e}")
    else:
        print("Skipping save_credentials in non-development environment. Manage credentials via platform environment variables.")


