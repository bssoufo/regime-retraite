# File: sharepoint_connector/sharepoint_uploader.py

from sharepoint_connector.auth import authenticate, get_headers, get_form_digest
from sharepoint_connector.sharepoint_utils import create_folder, upload_file_local
from sharepoint_connector.config import SITE_URL, TARGET_FOLDER_RELATIVE_URL
import os
from typing import List
from app.utils import send_email, get_user_name  # Import des fonctions utilitaires
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()  # Charger les variables d'environnement

def upload_files_to_sharepoint(local_directory: str, email: str) -> bool:
    """
    Uploads all files from a local directory to a SharePoint folder associated with the user's email.

    Sends notifications par e-mail en fonction du succès ou de l'échec de l'opération.

    Returns:
        bool: True si l'upload a réussi, False sinon.
    """
    try:
        # Authentication
        access_token = authenticate()
        headers = get_headers(access_token)
        form_digest = get_form_digest(SITE_URL, headers)

        # Créer le dossier cible dans SharePoint
        target_folder = f"/{TARGET_FOLDER_RELATIVE_URL}/{email.replace('@', '_')}"
        create_resp = create_folder(SITE_URL, target_folder, headers, form_digest)
        if create_resp.ok:
             print(f"Dossier SharePoint '{target_folder}' créé ou déjà existant.")
        else:
             if "already exists" in create_resp.text:
                print(f"Dossier SharePoint '{target_folder}' existe déjà.")
             else:
                print(f"Erreur lors de la création du dossier SharePoint '{target_folder}': {create_resp.text}")
                raise Exception(f"Erreur de création de dossier SharePoint: {create_resp.text}")
        
        # Upload de chaque fichier du répertoire local
        for filename in os.listdir(local_directory):
            local_file_path = os.path.join(local_directory, filename)
            if os.path.isfile(local_file_path):
                upload_local_resp = upload_file_local(SITE_URL, target_folder, local_file_path, headers, form_digest)
                if upload_local_resp.ok:
                    print(f"Fichier '{filename}' uploadé avec succès sur SharePoint.")
                else:
                    print(f"Erreur lors de l'upload du fichier '{filename}' sur SharePoint: {upload_local_resp.text}")
                    raise Exception(f"Erreur d'upload de fichier SharePoint: {upload_local_resp.text}")
        
        # Extraire le nom de l'utilisateur depuis le fichier d'identification
        user_name = get_user_name(local_directory)
        if not user_name:
            print("Nom de l'utilisateur non trouvé. Utilisation de l'adresse e-mail comme identifiant.")
            user_name = email.split('@')[0]  # Fallback si le nom n'est pas trouvé

        # Si tous les uploads ont réussi
        envoyer_notifications_success(email, user_name, target_folder)
        return True
    except Exception as e:
        print(f"Une erreur est survenue lors de l'upload: {e}")
        envoyer_notifications_failure(e, email)
        return False

def envoyer_notifications_success(user_email: str, user_name: str, sharepoint_folder: str):
    """
    Envoie des notifications par e-mail en cas de succès de l'upload.

    Args:
        user_email (str): Adresse e-mail de l'utilisateur.
        user_name (str): Nom de l'utilisateur.
        sharepoint_folder (str): Chemin du dossier SharePoint.
    """
    # Date actuelle
    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Contenu des e-mails
    # Email de confirmation à l'utilisateur
    subject_user = "Confirmation d'Upload vers SharePoint"
    template_user = "upload_success_user.html"
    context_user = {
        "user_name": user_name,
        "upload_date": upload_date
    }

    # Email informatif à l'équipe de régime retraite
    subject_regime = "Nouvel Upload de Fichiers"
    template_regime = "upload_success_regime.html"
    context_regime = {
        "user_name": user_name,
        "upload_date": upload_date,
        "sharepoint_folder": sharepoint_folder
    }

    # Récupération des adresses e-mail depuis les variables d'environnement
    regime_email = os.getenv("REGIME_RETRAITE_EMAIL")
    
    # Envoi des e-mails
    if regime_email:
        send_email(
            subject=subject_user,
            template_name=template_user,
            context=context_user,
            recipients=[user_email]
        )
        send_email(
            subject=subject_regime,
            template_name=template_regime,
            context=context_regime,
            recipients=[regime_email]
        )
    else:
        print("REGIME_RETRAITE_EMAIL n'est pas défini dans les variables d'environnement.")

def envoyer_notifications_failure(error: Exception, user_email: str):
    """
    Envoie une notification par e-mail en cas d'échec de l'upload.

    Args:
        error (Exception): L'exception survenue.
        user_email (str): Adresse e-mail de l'utilisateur.
    """
    # Date actuelle
    failure_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Contenu des e-mails
    subject_support = "Échec de l'Upload vers SharePoint"
    template_support = "upload_failure_support.html"
    context_support = {
        "user_email": user_email,
        "failure_date": failure_date,
        "error_message": str(error)
    }

    # Récupération des adresses e-mail de support depuis les variables d'environnement
    support_emails_str = os.getenv("SUPPORT_EMAILS", "")
    support_emails = [email.strip() for email in support_emails_str.split(",") if email.strip()]

    if support_emails:
        send_email(
            subject=subject_support,
            template_name=template_support,
            context=context_support,
            recipients=support_emails
        )
    else:
        print("SUPPORT_EMAILS n'est pas défini correctement dans les variables d'environnement.")
