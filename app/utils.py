import os
import uuid
from datetime import datetime
from typing import List
from fastapi import HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape


# Initialiser l'environnement Jinja2
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'email_templates')
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)


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
        print(f"Le fichier {identification_file} n'existe pas.")
        return None
    
    try:
        with open(identification_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Nom:"):
                    return line.split("Nom:")[1].strip()
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {identification_file}: {e}")
    
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
        print(f"Erreur lors du rendu du template {template_name}: {e}")
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
        print(f"Email envoyé à {recipients}")
    except Exception as e:
        print(f"Échec de l'envoi de l'e-mail à {recipients}: {e}")

