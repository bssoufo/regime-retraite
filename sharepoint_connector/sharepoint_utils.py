import os
import requests
from sharepoint_connector.config import SITE_URL

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
    response = requests.post(folder_endpoint, headers=post_headers, json=payload)
    return response

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
    with open(local_file_path, "rb") as f:
        file_content = f.read()
    response = requests.post(upload_endpoint, headers=post_headers, data=file_content)
    return response

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
