import os
import uuid
from datetime import datetime
from typing import List
from fastapi import HTTPException


def create_upload_directory(base_dir: str, email: str) -> str:
    """Creates a unique upload directory based on email and a UUID."""
    unique_id = str(uuid.uuid4())
    dir_name = f"{email.replace('@', '_')}-{unique_id}"
    upload_dir = os.path.join(base_dir, dir_name)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def create_identification_file(upload_dir: str, name: str, date_of_birth: str, email: str) -> None:
    """Creates the identification_client.txt file with client information."""
    file_path = os.path.join(upload_dir, "identification_client.txt")
    with open(file_path, "w") as f:
        f.write(f"Nom: {name}\n")
        f.write(f"Date de naissance: {date_of_birth}\n")
        f.write(f"Email: {email}\n")

def rename_file(upload_dir: str, original_filename: str, description: str) -> str:
    """Renames the file with description and current date."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    _, file_extension = os.path.splitext(original_filename)
    new_filename = f"{description}_{current_date}{file_extension}"
    new_file_path = os.path.join(upload_dir, new_filename)
    return new_file_path