import os
from dotenv import load_dotenv
from dotenv import find_dotenv

load_dotenv()
env_path = find_dotenv()
load_dotenv(override=True)
# Print the path
print(f"The path to the .env file is: {env_path}")
CLIENT_ID = os.getenv("CLIENT_ID")
TENANT = os.getenv("TENANT")
PFX_PATH = os.getenv("PFX_PATH")
PFX_ABSOLUTE_PATH = os.path.abspath(PFX_PATH)
print(PFX_PATH)
CERT_PASSWORD = os.getenv("CERT_PASSWORD")
SITE_URL = os.getenv("SITE_URL")
TARGET_FOLDER_RELATIVE_URL =os.getenv("TARGET_FOLDER_RELATIVE_URL")
SCOPE = os.getenv("SCOPE")
SCOPE = [SCOPE]
AUTHORITY = os.getenv("AUTHORITY")
RETRY_COUNT = int(os.getenv("RETRY_COUNT", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 5))  # seconds
