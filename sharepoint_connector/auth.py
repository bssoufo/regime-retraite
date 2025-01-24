import msal
import requests
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization
import os
from sharepoint_connector.config import CLIENT_ID, TENANT, PFX_PATH,PFX_ABSOLUTE_PATH,CERT_PASSWORD, SCOPE, AUTHORITY, SITE_URL
dossier_courant = os.getcwd()

def authenticate():
    # Charger le certificat PFX
    with open(PFX_ABSOLUTE_PATH, "rb") as f:
        pfx_data = f.read()

    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_data, CERT_PASSWORD.encode()
    )

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    thumbprint_bytes = certificate.fingerprint(certificate.signature_hash_algorithm)
    thumbprint = thumbprint_bytes.hex()

    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential={
            "private_key": private_key_pem.decode(),
            "thumbprint": thumbprint
        }
    )

    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        raise Exception(f"Impossible d'obtenir un jeton: {result.get('error')} - {result.get('error_description')}")
    return result["access_token"]

def get_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json;odata=verbose"
    }

def get_form_digest(site_url, headers):
    contextinfo_endpoint = f"{site_url}/_api/contextinfo"
    response = requests.post(contextinfo_endpoint, headers=headers)
    response.raise_for_status()
    return response.json()["d"]["GetContextWebInformation"]["FormDigestValue"]
