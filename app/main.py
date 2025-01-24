# File: app/main.py

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
from typing import List, Optional, Dict
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.utils import create_upload_directory, create_identification_file, rename_file, logger,envoyer_notification_erreur_systeme
from sharepoint_connector.sharepoint_uploader import upload_files_to_sharepoint
import traceback
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "*",  # ATTENTION : Soyez prudent avec '*' en production.
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
    logger.warning(f"UPLOAD_DIRECTORY not set in .env, using default: {UPLOAD_DIRECTORY}")

@app.post("/uploadfiles/")
async def create_upload_files(
    request: Request,
    name: str = Form(...),
    date_of_birth: str = Form(...),
    email: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()  # Ajout de BackgroundTasks
):
    if not UPLOAD_DIRECTORY:
        logger.error("UPLOAD_DIRECTORY is not configured.")
        raise Exception("UPLOAD_DIRECTORY is not configured.")

    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)
        logger.info(f"Created base upload directory: {UPLOAD_DIRECTORY}")

    uploaded_files_info = []
    files_data = []
    form_data = await request.form()  # Récupérer les données du formulaire

    # Debug : Afficher toutes les clés du formulaire et leurs types
    logger.debug("Form Data Keys and Types:")
    for key in form_data.keys():
        value = form_data.get(key)
        logger.debug(f"{key}: {type(value)}")

    file_index = 0
    while True:
        file_field_name = f"file_{file_index}"
        description_field_name = f"description_{file_index}"

        if file_field_name not in form_data:
            logger.info(f"No more files found after index {file_index - 1}.")
            break

        current_file = form_data[file_field_name]
        current_description = form_data.get(description_field_name)

        logger.debug(f"Processing {file_field_name}: {current_file}")
        logger.debug(f"Is UploadFile: {isinstance(current_file, UploadFile)}")
        
        files_data.append({
            "file": current_file,
            "description": current_description or None
        })
        file_index += 1

    if not files_data:
        logger.warning("No valid files uploaded.")
        raise HTTPException(status_code=400, detail="No valid files uploaded.")

    upload_dir = create_upload_directory(UPLOAD_DIRECTORY, email)
    create_identification_file(upload_dir, name, date_of_birth, email)

    for file_data in files_data:
        file = file_data["file"]
        description = file_data["description"]

        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension not in ALLOWED_EXTENSIONS:
            logger.warning(f"File type not allowed for file: {file.filename}. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed for file: {file.filename}. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Renommer le fichier avec le nom original et l'horodatage
        new_filename = rename_file(upload_dir, file.filename, description)
        
        # Déterminer le répertoire où sauvegarder le fichier
        if description:
            description_dir = os.path.join(upload_dir, description)
            os.makedirs(description_dir, exist_ok=True)
            logger.info(f"Created description directory: {description_dir}")
            file_save_path = os.path.join(description_dir, os.path.basename(new_filename))
        else:
            file_save_path = new_filename

        try:
            with open(file_save_path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # Lire par morceaux de 1MB
                    if not chunk:
                        break
                    f.write(chunk)
            file_info = {
                "original_filename": file.filename,
                "content_type": file.content_type,
                "saved_path": file_save_path,
                "description": description
            }
            uploaded_files_info.append(file_info)
            logger.info(f"Saved file {file.filename} to {file_save_path}")
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file {file.filename}: {e}")
        finally:
            await file.close()
    
    background_tasks.add_task(upload_files_to_sharepoint, upload_dir, email)  # Lancer l'upload vers SharePoint en arrière-plan
    logger.info(f"Initiated SharePoint upload for directory: {upload_dir}")

    response = {
        "name": name,
        "date_of_birth": date_of_birth,
        "email": email,
        "uploaded_files_info": uploaded_files_info,
        "message": "Files uploaded and saved successfully! SharePoint upload initiated in the background."
    }

    logger.info(f"Upload response: {response}")
    return response

@app.get("/cause-error")
async def cause_error():
    raise ValueError("Ceci est une erreur de test.")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Gestionnaire d'exceptions global pour capturer toutes les exceptions non traitées.
    """
    # Enregistrer l'erreur avec la trace complète
    error_trace = traceback.format_exc()
    logger.error(f"Exception non gérée: {exc}\nTraceback: {error_trace}")

    # Extraire l'adresse e-mail de l'utilisateur si disponible
    try:
        form = await request.form()
        user_email = form.get("email", "Inconnu")
    except Exception:
        user_email = "Inconnu"

    # Envoyer la notification d'erreur en arrière-plan
    background_tasks = BackgroundTasks()
    background_tasks.add_task(envoyer_notification_erreur_systeme, user_email, exc, error_trace)

    # Retourner une réponse générique au client
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne s'est produite. L'équipe de support a été notifiée."},
        background=background_tasks
    )