# File: app/main.py

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request, Security
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
from datetime import date
import os
import uuid
import traceback
from fastapi import Depends
from fastapi import HTTPException, Security, status

from dotenv import load_dotenv

from app.utils import (
    create_upload_directory,
    create_identification_file,
    rename_file,
    logger,
    envoyer_notification_erreur_systeme,
    get_api_key,
    get_user_email,
    API_KEY_NAME
)

from sharepoint_connector.sharepoint_uploader import upload_files_to_sharepoint

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
ALLOWED_EXTENSIONS_STR = os.getenv("ALLOWED_EXTENSIONS_STR", ".pdf,.docx,.xlsx,.jpg,.jpeg,.png,.gif")
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
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Endpoint pour uploader des fichiers. Protégé par un token de sécurité.
    """
    if not UPLOAD_DIRECTORY:
        logger.error("UPLOAD_DIRECTORY is not configured.")
        raise Exception("UPLOAD_DIRECTORY is not configured.")

    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)
        logger.info(f"Created base upload directory: {UPLOAD_DIRECTORY}")

    uploaded_files_info = []
    files_data = []
    form_data = await request.form()  # Get form data

    # Debug: Print all form keys and their types
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

# Gestionnaire d'exceptions global
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
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """
    Middleware pour valider le token de sécurité pour chaque requête.
    """
    try:
        # Extraire le token depuis les en-têtes
        api_key = request.headers.get(API_KEY_NAME)
        if not api_key:
            logger.warning("Token de sécurité manquant dans les en-têtes de la requête.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de sécurité manquant.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        expected_api_key = os.getenv("API_SECURITY_TOKEN")
        if api_key != expected_api_key:
            logger.warning("Token de sécurité invalide fourni.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de sécurité invalide.",
            )
        
        # Si le token est valide, continuez le traitement de la requête
        response = await call_next(request)
        return response
    except HTTPException as http_exc:
        # Gérer les exceptions HTTP
        return JSONResponse(
            status_code=http_exc.status_code,
            content={"detail": http_exc.detail},
        )
    except Exception as e:
        # Gérer les autres exceptions
        error_trace = traceback.format_exc()
        logger.error(f"Exception dans le middleware de sécurité: {e}\nTraceback: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Une erreur interne s'est produite. L'équipe de support a été notifiée."},
        )
@app.get("/cause-error")
async def cause_error():
    raise ValueError("Ceci est une erreur de test.")

@app.post("/retry-failed-uploads/")
async def retry_failed_uploads(background_tasks: BackgroundTasks):
    """
    Endpoint pour relancer les uploads échoués.
    Parcourt tous les dossiers dans `uploaded_files/` et relance le processus
    d'upload vers SharePoint si le dossier existe encore.
    """
    if not os.path.exists(UPLOAD_DIRECTORY):
        # S'il n'y a pas de dossier du tout, on retourne un message sans erreur
        return {"message": f"Le répertoire {UPLOAD_DIRECTORY} n'existe pas ou est vide."}
    
    # Récupérer la liste de tous les dossiers dans UPLOAD_DIRECTORY
    subdirs = [
        os.path.join(UPLOAD_DIRECTORY, d) for d in os.listdir(UPLOAD_DIRECTORY)
        if os.path.isdir(os.path.join(UPLOAD_DIRECTORY, d))
    ]
    
    if not subdirs:
        return {"message": "Aucun dossier à relancer. Tous les uploads sont peut-être déjà traités."}
    
    # Pour accumuler des informations sur ce qui va être relancé
    relaunch_info = []
    
    for subdir in subdirs:
        # On récupère l'email en lisant identification_client.txt
        user_email = get_user_email(subdir)
        if not user_email:
            # Si pas d'email, on ignore ou on log un warning
            logger.warning(f"Aucun email trouvé dans le dossier {subdir}. Upload non relancé.")
            continue
        
        # Ajout de la tâche d'upload en arrière-plan
        background_tasks.add_task(upload_files_to_sharepoint, subdir, user_email)
        relaunch_info.append({
            "folder": subdir,
            "email": user_email,
            "status": "Relance programmée"
        })
    
    # Réponse de l'API
    return {
        "message": "La relance des uploads échoués a été lancée en arrière-plan.",
        "details": relaunch_info
    }