import asyncio
from pathlib import Path
from typing import Optional
import httpx
import msal
from app.config import get_settings

settings = get_settings()

# Caché del access token en memoria (expira ~1h, MSAL lo renueva solo)
_msal_app: Optional[msal.ConfidentialClientApplication] = None


def _get_msal_app() -> msal.ConfidentialClientApplication:
    global _msal_app
    if _msal_app is None:
        # Para cuentas personales de Microsoft usar "consumers"
        # Para cuentas organizacionales usar el tenant_id específico
        authority = f"https://login.microsoftonline.com/consumers"
        _msal_app = msal.ConfidentialClientApplication(
            settings.onedrive_client_id,
            authority=authority,
            client_credential=settings.onedrive_client_secret,
        )
    return _msal_app


def _get_access_token() -> Optional[str]:
    """
    Obtiene un access token usando el refresh_token almacenado.
    El refresh_token se obtiene una sola vez ejecutando scripts/get_onedrive_token.py.
    """
    if not all([
        settings.onedrive_client_id,
        settings.onedrive_client_secret,
        settings.onedrive_refresh_token,
    ]):
        return None

    app = _get_msal_app()
    scopes = ["https://graph.microsoft.com/Files.ReadWrite", "offline_access"]

    # Intentar con el refresh_token
    result = app.acquire_token_by_refresh_token(
        settings.onedrive_refresh_token,
        scopes=scopes,
    )

    if "access_token" in result:
        return result["access_token"]

    # Si falla, loguear el error
    error = result.get("error_description", result.get("error", "unknown"))
    raise Exception(f"No se pudo obtener access token de OneDrive: {error}")


async def upload_file(local_path: Path, remote_filename: str) -> Optional[str]:
    """
    Sube un archivo al OneDrive personal y retorna el enlace compartible.
    Usa Microsoft Graph API con refresh_token (delegated flow para cuentas personales).
    """
    token = await asyncio.to_thread(_get_access_token)
    if not token:
        return None

    folder = settings.onedrive_folder_path.strip("/")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
    }

    # Para cuentas personales de Microsoft usar /me/drive (token delegado)
    upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder}/{remote_filename}:/content"

    with open(local_path, "rb") as f:
        content = f.read()

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.put(upload_url, content=content, headers=headers)
        if resp.status_code not in (200, 201):
            raise Exception(f"OneDrive upload failed: {resp.status_code} {resp.text}")
        item = resp.json()
        item_id = item.get("id")

    # Crear enlace compartible
    share_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/createLink"
    async with httpx.AsyncClient(timeout=15) as client:
        share_resp = await client.post(
            share_url,
            json={"type": "view", "scope": "anonymous"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        if share_resp.status_code in (200, 201):
            link_data = share_resp.json()
            return link_data.get("link", {}).get("webUrl")

    return item.get("webUrl")


async def upload_evidence(local_path: Path, bitacora_number: int, filename: str) -> Optional[str]:
    """Sube un archivo de evidencia al OneDrive bajo la carpeta de la bitácora."""
    folder = settings.onedrive_folder_path.strip("/")
    remote_name = f"Bitacora{bitacora_number}/{filename}"
    return await upload_file(local_path, remote_name)


def is_configured() -> bool:
    return bool(
        settings.onedrive_client_id
        and settings.onedrive_client_secret
        and settings.onedrive_refresh_token
    )
