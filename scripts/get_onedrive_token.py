"""
Script para obtener el refresh_token de OneDrive personal.
Ejecutar UNA VEZ localmente:

    python scripts/get_onedrive_token.py

Luego copiar ONEDRIVE_REFRESH_TOKEN en las variables de entorno de Coolify.
"""
import msal
import json
import os

# Device code flow = flujo público (no necesita client_secret)
CLIENT_ID = os.getenv("ONEDRIVE_CLIENT_ID") or input("ONEDRIVE_CLIENT_ID: ").strip()

# Para cuentas personales de Microsoft (Gmail, Hotmail, Outlook personal)
AUTHORITY = "https://login.microsoftonline.com/consumers"

# Scopes para OneDrive personal
SCOPES = ["Files.ReadWrite"]  # offline_access lo agrega MSAL automáticamente

app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

flow = app.initiate_device_flow(scopes=SCOPES)

if "user_code" not in flow:
    print("Error iniciando device flow:", flow)
    exit(1)

print("\n" + "=" * 60)
print("PASO 1: Abre este enlace en el navegador:")
print(f"  {flow['verification_uri']}")
print(f"\nPASO 2: Ingresa el código: {flow['user_code']}")
print(f"\nPASO 3: Inicia sesión con tu cuenta de Microsoft personal")
print("=" * 60)
print("\nEsperando que inicies sesión...")

result = app.acquire_token_by_device_flow(flow)

if "access_token" not in result:
    print("Error obteniendo token:", result.get("error_description", result))
    exit(1)

refresh_token = result.get("refresh_token", "")
access_token = result.get("access_token", "")

print("\n" + "=" * 60)
print("TOKEN OBTENIDO EXITOSAMENTE")
print("=" * 60)
print(f"\nREFRESH_TOKEN (copia esto en Coolify como ONEDRIVE_REFRESH_TOKEN):")
print(refresh_token)
print("\nGuardando en onedrive_tokens.json...")

with open("onedrive_tokens.json", "w") as f:
    json.dump({
        "access_token": access_token[:50] + "...",
        "refresh_token": refresh_token,
        "scopes": result.get("scope", ""),
    }, f, indent=2)

print("\nListo. Agrega esta variable en Coolify:")
print(f"  ONEDRIVE_REFRESH_TOKEN={refresh_token}")
print("\nNO compartas este token — tiene acceso a tu OneDrive.")
