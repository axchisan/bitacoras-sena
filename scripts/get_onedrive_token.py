"""
Script para obtener el refresh_token de OneDrive personal.
Ejecutar UNA VEZ localmente:

    pip install msal
    python scripts/get_onedrive_token.py

Luego copiar el REFRESH_TOKEN en las variables de entorno de Coolify.
"""
import msal
import json
import os

# Credenciales de la Azure App Registration (bitacoras-sena)
# Leer desde variables de entorno o pedir al usuario
CLIENT_ID = os.getenv("ONEDRIVE_CLIENT_ID") or input("ONEDRIVE_CLIENT_ID: ").strip()
CLIENT_SECRET = os.getenv("ONEDRIVE_CLIENT_SECRET") or input("ONEDRIVE_CLIENT_SECRET: ").strip()

# Para cuentas personales de Microsoft (Gmail, Hotmail, Outlook personal)
# usar "consumers". Para cuentas mixtas usar "common".
AUTHORITY = "https://login.microsoftonline.com/consumers"

# Scopes para OneDrive personal
SCOPES = ["Files.ReadWrite", "offline_access"]

app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)

# Device code flow: el usuario introduce un código en microsoft.com/devicelogin
flow = app.initiate_device_flow(scopes=SCOPES)

if "user_code" not in flow:
    print("Error iniciando device flow:", flow)
    exit(1)

print("\n" + "="*60)
print("PASO 1: Abre este enlace en el navegador:")
print(f"  {flow['verification_uri']}")
print(f"\nPASO 2: Ingresa el código: {flow['user_code']}")
print(f"\nPASO 3: Inicia sesión con tu cuenta de Microsoft personal")
print(f"  (la vinculada a arciniegasgerenaduvanyair@gmail.com)")
print("="*60 + "\n")

result = app.acquire_token_by_device_flow(flow)

if "access_token" not in result:
    print("Error obteniendo token:", result.get("error_description", result))
    exit(1)

refresh_token = result.get("refresh_token", "")
access_token = result.get("access_token", "")

print("\n" + "="*60)
print("TOKEN OBTENIDO EXITOSAMENTE")
print("="*60)
print(f"\nREFRESH_TOKEN (copia esto en Coolify como ONEDRIVE_REFRESH_TOKEN):")
print(refresh_token)
print("\nGuardando en onedrive_tokens.json para referencia...")

with open("onedrive_tokens.json", "w") as f:
    json.dump({
        "access_token": access_token[:50] + "...",
        "refresh_token": refresh_token,
        "scopes": result.get("scope", ""),
    }, f, indent=2)

print("\nListo. Agrega esta variable en Coolify:")
print(f"  ONEDRIVE_REFRESH_TOKEN={refresh_token}")
print("\n⚠️  NO compartas este token. Tiene acceso a tu OneDrive.")
