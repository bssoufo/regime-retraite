# File: sharepoint_connector/sharepoint_uploader.py

from sharepoint_connector.auth import authenticate, get_headers, get_form_digest
from sharepoint_connector.sharepoint_utils import create_folder, upload_file_local
from sharepoint_connector.config import SITE_URL, TARGET_FOLDER_RELATIVE_URL
import os
from typing import List
from app.utils import send_email, get_user_name, logger  # Import du logger
from dotenv import load_dotenv
from datetime import datetime
import shutil  # Import pour supprimer les dossiers

load_dotenv()  # Charger les variables d'environnement

def upload_files_to_sharepoint(local_directory: str, email: str) -> bool:
    """
    Uploads all files and folders from a local directory to a SharePoint folder associated with the user's email.

    Sends email notifications based on the success or failure of the operation.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    try:
        # Authentication
        access_token = authenticate()
        headers = get_headers(access_token)
        form_digest = get_form_digest(SITE_URL, headers)

        # Créer le dossier cible dans SharePoint
        target_folder = f"/{TARGET_FOLDER_RELATIVE_URL}/{email}"  # Ne plus remplacer '@' par '_'
        create_resp = create_folder(SITE_URL, target_folder, headers, form_digest)
        if create_resp.ok:
            logger.info(f"Dossier SharePoint '{target_folder}' créé ou déjà existant.")
        else:
            if "already exists" in create_resp.text.lower():
                logger.info(f"Dossier SharePoint '{target_folder}' existe déjà.")
            else:
                logger.error(f"Erreur lors de la création du dossier SharePoint '{target_folder}': {create_resp.text}")
                raise Exception(f"Erreur de création de dossier SharePoint: {create_resp.text}")
        
        # Parcourir le répertoire local récursivement
        for root, dirs, files in os.walk(local_directory):
            # Calculer le chemin relatif depuis local_directory
            rel_path = os.path.relpath(root, local_directory)
            if rel_path == ".":
                rel_path = ""
            # Correspondant dossier SharePoint
            sharepoint_folder = os.path.join(target_folder, rel_path).replace("\\", "/")
            if rel_path != "":
                # Créer le dossier SharePoint s'il n'est pas le dossier racine
                create_resp = create_folder(SITE_URL, sharepoint_folder, headers, form_digest)
                if create_resp.ok:
                    logger.info(f"Dossier SharePoint '{sharepoint_folder}' créé ou déjà existant.")
                else:
                    if "already exists" in create_resp.text.lower():
                        logger.info(f"Dossier SharePoint '{sharepoint_folder}' existe déjà.")
                    else:
                        logger.error(f"Erreur lors de la création du dossier SharePoint '{sharepoint_folder}': {create_resp.text}")
                        raise Exception(f"Erreur de création de dossier SharePoint: {create_resp.text}")
            
            # Upload des fichiers dans le dossier actuel
            for filename in files:
                local_file_path = os.path.join(root, filename)
                upload_local_resp = upload_file_local(SITE_URL, sharepoint_folder, local_file_path, headers, form_digest)
                if upload_local_resp.ok:
                    logger.info(f"Fichier '{filename}' uploadé avec succès sur SharePoint dans '{sharepoint_folder}'.")
                else:
                    logger.error(f"Erreur lors de l'upload du fichier '{filename}' sur SharePoint dans '{sharepoint_folder}': {upload_local_resp.text}")
                    raise Exception(f"Erreur d'upload de fichier SharePoint: {upload_local_resp.text}")
        
        # Extraire le nom de l'utilisateur depuis le fichier d'identification
        user_name = get_user_name(local_directory)
        if not user_name:
            logger.warning("Nom de l'utilisateur non trouvé. Utilisation de l'adresse e-mail comme identifiant.")
            user_name = email.split('@')[0]  # Fallback si le nom n'est pas trouvé

        # Chemin du dossier SharePoint pour les e-mails (dossier racine cible)
        sharepoint_folder_email = target_folder

        # Si tous les uploads ont réussi
        envoyer_notifications_success(email, user_name, sharepoint_folder_email)

        # Supprimer le dossier temporaire sur le disque
        try:
            shutil.rmtree(local_directory)
            logger.info(f"Dossier temporaire '{local_directory}' supprimé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du dossier temporaire '{local_directory}': {e}")

        return True
    except Exception as e:
        logger.error(f"Une erreur est survenue lors de l'upload: {e}")
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
        try:
            send_email(
                subject=subject_user,
                template_name=template_user,
                context=context_user,
                recipients=[user_email]
            )
            logger.info(f"Email de confirmation envoyé à l'utilisateur: {user_email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de confirmation à {user_email}: {e}")
        
        try:
            send_email(
                subject=subject_regime,
                template_name=template_regime,
                context=context_regime,
                recipients=[regime_email]
            )
            logger.info(f"Email informatif envoyé à l'équipe de Régime Retraite: {regime_email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email informatif à {regime_email}: {e}")
    else:
        logger.warning("REGIME_RETRAITE_EMAIL n'est pas défini dans les variables d'environnement.")

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
        try:
            send_email(
                subject=subject_support,
                template_name=template_support,
                context=context_support,
                recipients=support_emails
            )
            logger.info(f"Email de notification d'échec envoyé à: {support_emails}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de notification d'échec à {support_emails}: {e}")
    else:
        logger.warning("SUPPORT_EMAILS n'est pas défini correctement dans les variables d'environnement.")
