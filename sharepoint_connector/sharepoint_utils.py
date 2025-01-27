# File: sharepoint_connector/sharepoint_utils.py

import os
import requests
import time
from sharepoint_connector.config import RETRY_COUNT, RETRY_DELAY
from app.utils import logger

def create_folder(site_url, target_folder_relative_url, headers, form_digest_value):
    post_headers = headers.copy()
    post_headers.update({
        "Content-Type": "application/json;odata=verbose",
        "X-RequestDigest": form_digest_value
    })
    folder_endpoint = f"{site_url}/_api/web/folders"
    payload = {
        "__metadata": {"type": "SP.Folder"},
        "ServerRelativeUrl": target_folder_relative_url
    }

    for attempt in range(RETRY_COUNT + 1):
        try:
            response = requests.post(folder_endpoint, headers=post_headers, json=payload)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < RETRY_COUNT:
                logger.warning(
                    f"Attempt {attempt+1}/{RETRY_COUNT+1} failed to create folder {target_folder_relative_url}. "
                    f"Retrying in {RETRY_DELAY}s. Error: {str(e)}"
                )
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"All attempts failed to create folder {target_folder_relative_url}")
                raise

def upload_file_local(site_url, target_folder_relative_url, local_file_path, headers, form_digest_value):
    post_headers = headers.copy()
    post_headers.update({
        "Content-Type": "application/octet-stream",
        "X-RequestDigest": form_digest_value
    })
    filename = os.path.basename(local_file_path)
    upload_endpoint = (
        f"{site_url}/_api/web/GetFolderByServerRelativeUrl('{target_folder_relative_url}')"
        f"/Files/add(url='{filename}',overwrite=true)"
    )

    for attempt in range(RETRY_COUNT + 1):
        try:
            with open(local_file_path, "rb") as f:
                file_content = f.read()
            response = requests.post(upload_endpoint, headers=post_headers, data=file_content)
            response.raise_for_status()
            return response
        except (requests.exceptions.RequestException, IOError) as e:
            if attempt < RETRY_COUNT:
                logger.warning(
                    f"Attempt {attempt+1}/{RETRY_COUNT+1} failed to upload {filename}. "
                    f"Retrying in {RETRY_DELAY}s. Error: {str(e)}"
                )
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"All attempts failed to upload {filename}")
                raise
def upload_file_from_url(site_url, target_folder_relative_url, file_url, headers, form_digest_value):
    post_headers = headers.copy()
    post_headers.update({
        "Content-Type": "application/octet-stream",
        "X-RequestDigest": form_digest_value
    })
    filename = os.path.basename(file_url)
    upload_endpoint = (
        f"{site_url}/_api/web/GetFolderByServerRelativeUrl('{target_folder_relative_url}')"
        f"/Files/add(url='{filename}',overwrite=true)"
    )
    file_response = requests.get(file_url)
    file_response.raise_for_status()
    file_content = file_response.content
    response = requests.post(upload_endpoint, headers=post_headers, data=file_content)
    return response
