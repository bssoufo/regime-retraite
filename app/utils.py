# File: app/utils.py

import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from logging.handlers import TimedRotatingFileHandler
import logging
import shutil


# Initialiser l'environnement Jinja2
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'email_templates')
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)


# Configuration du Logging
LOG_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', 'logs')
ARCHIVE_DIRECTORY = os.path.join(LOG_DIRECTORY, 'archive')

# Créer les dossiers de log et d'archive s'ils n'existent pas
os.makedirs(LOG_DIRECTORY, exist_ok=True)
os.makedirs(ARCHIVE_DIRECTORY, exist_ok=True)

class ArchivingTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Gestionnaire de fichiers de log qui archive les fichiers de log après rotation.
    """
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None, delay=False, utc=False, atTime=None):
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc, atTime)

    def doRollover(self):
        super().doRollover()
        # Déplacer le fichier de log rotaté dans le dossier d'archive
        if self.backupCount > 0:
            for i in range(self.backupCount, 0, -1):
                sfn = f"{self.baseFilename}.{self.extMatch.match(str(i))}"
                dfn = os.path.join(ARCHIVE_DIRECTORY, os.path.basename(sfn))
                if os.path.exists(sfn):
                    shutil.move(sfn, dfn)



# Configuration du Logger
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)

# Création du gestionnaire de fichiers de log avec rotation quotidienne
log_file = os.path.join(LOG_DIRECTORY, 'app.log')
handler = ArchivingTimedRotatingFileHandler(
    log_file,
    when='midnight',
    interval=1,
    backupCount=30,  # Nombre de fichiers de log à conserver dans l'archive
    encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def create_upload_directory(base_dir: str, email: str) -> str:
    """Creates a unique upload directory based on email and a UUID without replacing '@'."""
    unique_id = str(uuid.uuid4())
    dir_name = f"{email}-{unique_id}"  # Ne plus remplacer '@' par '_'
    upload_dir = os.path.join(base_dir, dir_name)
    os.makedirs(upload_dir, exist_ok=True)
    logger.info(f"Created upload directory: {upload_dir}")
    return upload_dir

def create_identification_file(upload_dir: str, name: str, date_of_birth: str, email: str) -> None:
    """Creates the identification_client.txt file with client information."""
    file_path = os.path.join(upload_dir, "identification_client.txt")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Nom: {name}\n")
            f.write(f"Date de naissance: {date_of_birth}\n")
            f.write(f"Email: {email}\n")
        logger.info(f"Created identification file at: {file_path}")
    except Exception as e:
        logger.error(f"Failed to create identification file at {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create identification file.")

def rename_file(upload_dir: str, original_filename: str, description: str) -> str:
    """
    Renomme le fichier en utilisant le nom original et un horodatage de réception.

    Format: nom_original_timestamp_de_reception.ext

    Args:
        upload_dir (str): Chemin vers le répertoire d'upload.
        original_filename (str): Nom original du fichier.
        description (str): Description du fichier (non utilisée dans le renommage).

    Returns:
        str: Chemin complet du fichier renommé.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    name, file_extension = os.path.splitext(original_filename)
    new_filename = f"{name}_{timestamp}{file_extension}"
    new_file_path = os.path.join(upload_dir, new_filename)
    logger.info(f"Renamed file '{original_filename}' to '{new_filename}'")
    return new_file_path

def get_user_name(upload_dir: str) -> Optional[str]:
    """
    Extrait le nom de l'utilisateur depuis le fichier identification_client.txt.
    
    Args:
        upload_dir (str): Chemin vers le répertoire d'upload de l'utilisateur.
    
    Returns:
        Optional[str]: Nom de l'utilisateur si trouvé, sinon None.
    """
    identification_file = os.path.join(upload_dir, "identification_client.txt")
    if not os.path.isfile(identification_file):
        logger.warning(f"Le fichier {identification_file} n'existe pas.")
        return None
    
    try:
        with open(identification_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Nom:"):
                    name = line.split("Nom:")[1].strip()
                    logger.info(f"Extracted user name: {name}")
                    return name
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier {identification_file}: {e}")
    
    return None

def send_email(subject: str, template_name: str, context: dict, recipients: List[str], sender_name: Optional[str] = None, sender_email: Optional[str] = None):
    """
    Envoie un e-mail au format HTML en utilisant un template.

    Args:
        subject (str): Sujet de l'e-mail.
        template_name (str): Nom du fichier template HTML.
        context (dict): Dictionnaire des variables à injecter dans le template.
        recipients (List[str]): Liste des destinataires.
        sender_name (Optional[str]): Nom de l'expéditeur. Si non spécifié, utilise SMTP_SENDER_NAME.
        sender_email (Optional[str]): Adresse e-mail de l'expéditeur. Si non spécifié, utilise SMTP_SENDER_EMAIL.
    """
    sender_name = sender_name or os.getenv("SMTP_SENDER_NAME")
    sender_email = sender_email or os.getenv("SMTP_SENDER_EMAIL")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Charger et rendre le template avec le contexte
    try:
        template = env.get_template(template_name)
        html_content = template.render(context)
    except Exception as e:
        logger.error(f"Erreur lors du rendu du template {template_name}: {e}")
        raise

    msg = MIMEMultipart()
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject

    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, recipients, msg.as_string())
        logger.info(f"Email envoyé à {recipients} avec le sujet '{subject}'")
    except Exception as e:
        logger.error(f"Échec de l'envoi de l'e-mail à {recipients}: {e}")


def envoyer_notification_erreur_systeme(user_email: str, error: Exception, traceback_str: str):
    """
    Envoie une notification par e-mail en cas d'erreur système.

    Args:
        user_email (str): Adresse e-mail de l'utilisateur concerné (si disponible).
        error (Exception): L'exception survenue.
        traceback_str (str): La trace complète de l'exception.
    """
    subject_support = "Erreur Système dans l'Application"
    template_support = "system_error_support.html"
    context_support = {
        "user_email": user_email,
        "error_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error_message": str(error),
        "traceback": traceback_str
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
            logger.info(f"Notification d'erreur système envoyée à: {support_emails}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification d'erreur système à {support_emails}: {e}")
    else:
        logger.warning("SUPPORT_EMAILS n'est pas défini correctement dans les variables d'environnement.")
