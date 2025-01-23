from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from typing import List, Optional, Dict
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "*",  # WARNING: Be cautious with '*' in production.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIRECTORY = os.getenv("UPLOAD_DIRECTORY")
ALLOWED_EXTENSIONS_STR = os.getenv("ALLOWED_EXTENSIONS", ".pdf,.docx,.xlsx,.jpg,.jpeg,.png,.gif")
ALLOWED_EXTENSIONS = [ext.strip().lower() for ext in ALLOWED_EXTENSIONS_STR.split(',')]

if not UPLOAD_DIRECTORY:
    UPLOAD_DIRECTORY = "uploaded_files"
    print(f"Warning: UPLOAD_DIRECTORY not set in .env, using default: {UPLOAD_DIRECTORY}")


@app.post("/uploadfiles/")
async def create_upload_files(
    request: Request,
    name: str = Form(...),
    date_of_birth: str = Form(...),
    email: str = Form(...)
):
    if not UPLOAD_DIRECTORY:
        raise Exception("UPLOAD_DIRECTORY is not configured.")

    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)

    uploaded_files_info = []
    files_data = []
    form_data = await request.form()  # Get form data
    
    # Debug: Print all form keys and their types
    print("Form Data Keys and Types:")
    for key in form_data.keys():
        value = form_data.get(key)
        print(f"{key}: {type(value)}")
    
    file_index = 0
    while True:
        file_field_name = f"file_{file_index}"
        description_field_name = f"description_{file_index}"

        if file_field_name not in form_data:
            print(f"No more files found after index {file_index - 1}.")
            break

        current_file = form_data[file_field_name]
        current_description = form_data.get(description_field_name)


        print(f"current_file type: {type(current_file)}")
        print(f"UploadFile class: {UploadFile}")
        print(f"current_file isinstance UploadFile: {isinstance(current_file, UploadFile)}")
        print(f"UploadFile ID: {id(UploadFile)}")
        print(f"current_file UploadFile ID: {id(current_file.__class__)}")
            
        print(f"Processing {file_field_name}: {current_file}")
        print(f"Is UploadFile: {isinstance(current_file, UploadFile)}")
        
      
        files_data.append({
                "file": current_file,
                "description": current_description or None
            })
        file_index += 1
      

    if not files_data:
        raise HTTPException(status_code=400, detail="No valid files uploaded.")

    for file_data in files_data:
        file = file_data["file"]
        description = file_data["description"]

        file_uuid = uuid.uuid4()
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed for file: {file.filename}. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        saved_filename = f"{file_uuid}{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, saved_filename)

        try:
            with open(file_path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # Read in 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)
            file_info = {
                "original_filename": file.filename,
                "content_type": file.content_type,
                "saved_path": file_path,
                "description": description
            }
            uploaded_files_info.append(file_info)
            print(f"Saved file {file.filename} to {file_path}")
        except Exception as e:
            print(f"Error saving file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file {file.filename}: {e}")
        finally:
            await file.close()

    dd = {
        "name": name,
        "date_of_birth": date_of_birth,
        "email": email,
        "uploaded_files_info": uploaded_files_info,
        "message": "Files uploaded and saved successfully!"
    }

    print(dd)
    return {
        "name": name,
        "date_of_birth": date_of_birth,
        "email": email,
        "uploaded_files_info": uploaded_files_info,
        "message": "Files uploaded and saved successfully!"
    }
