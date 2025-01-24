from sharepoint_connector.auth import authenticate, get_headers, get_form_digest
from sharepoint_connector.sharepoint_utils import create_folder, upload_file_local
from sharepoint_connector.config import SITE_URL, TARGET_FOLDER_RELATIVE_URL
import os
from typing import List

def upload_files_to_sharepoint(local_directory: str, email: str) -> bool:  # Return a boolean indicating success
    """
    Uploads all files from a local directory to a SharePoint folder associated with the user's email.
    
    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    try:
        # Authentication
        access_token = authenticate()
        headers = get_headers(access_token)
        form_digest = get_form_digest(SITE_URL, headers)

        # Create target folder in SharePoint with the email as a subfolder
        target_folder = f"/{TARGET_FOLDER_RELATIVE_URL}/{email.replace('@', '_')}"
        create_resp = create_folder(SITE_URL, target_folder, headers, form_digest)
        if create_resp.ok:
             print(f"SharePoint folder '{target_folder}' created or already exists.")
        else:
             if "already exists" in create_resp.text:
                print(f"SharePoint folder '{target_folder}' already exists.")
             else:
                print(f"Error creating SharePoint folder '{target_folder}': {create_resp.text}")
                return False  # Indicate failure
        
        # Upload each file from local directory
        for filename in os.listdir(local_directory):
            local_file_path = os.path.join(local_directory, filename)
            if os.path.isfile(local_file_path):
                upload_local_resp = upload_file_local(SITE_URL, target_folder, local_file_path, headers, form_digest)
                if upload_local_resp.ok:
                    print(f"File '{filename}' uploaded successfully to SharePoint.")
                else:
                    print(f"Error uploading file '{filename}' to SharePoint: {upload_local_resp.text}")
                    return False  # Indicate failure
        return True # All files uploaded successfully
    except Exception as e:
        print(f"An unexpected error occurred during the upload: {e}")
        return False  # Indicate failure

if __name__ == "__main__":
    # Example Usage (for testing only)
    example_directory = r"C:\Users\vladislav.tsurkan\Documents\upload_files\placeholder_domain.com-174520d1-836f-4c6c-89c1-35a4d0d8376a"  # Replace with your local test directory
    example_email = "placeholder@domain.com"  # Replace with your test email
    if upload_files_to_sharepoint(example_directory, example_email):
        print("Example upload completed successfully.")
    else:
        print("Example upload failed.")