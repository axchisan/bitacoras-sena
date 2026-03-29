from pathlib import Path
from typing import Optional
import httpx
import msal
from app.config import get_settings

settings = get_settings()


def _get_access_token() -> Optional[str]:
    if not all([settings.onedrive_client_id, settings.onedrive_client_secret, settings.onedrive_tenant_id]):
        return None

    authority = f"https://login.microsoftonline.com/{settings.onedrive_tenant_id}"
    app = msal.ConfidentialClientApplication(
        settings.onedrive_client_id,
        authority=authority,
        client_credential=settings.onedrive_client_secret,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result.get("access_token")


async def upload_file(local_path: Path, remote_filename: str) -> Optional[str]:
    """
    Upload a file to OneDrive and return the shareable link.
    Uses Microsoft Graph API with app-level permissions.
    """
    token = _get_access_token()
    if not token:
        return None

    folder = settings.onedrive_folder_path.strip("/")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"}

    upload_url = (
        f"https://graph.microsoft.com/v1.0/me/drive/root:/"
        f"{folder}/{remote_filename}:/content"
    )

    with open(local_path, "rb") as f:
        content = f.read()

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.put(upload_url, content=content, headers=headers)
        if resp.status_code not in (200, 201):
            raise Exception(f"OneDrive upload failed: {resp.status_code} {resp.text}")
        item = resp.json()
        item_id = item.get("id")

    # Create a shareable link
    share_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/createLink"
    async with httpx.AsyncClient(timeout=15) as client:
        share_resp = await client.post(
            share_url,
            json={"type": "view", "scope": "organization"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        if share_resp.status_code in (200, 201):
            link_data = share_resp.json()
            return link_data.get("link", {}).get("webUrl")

    return item.get("webUrl")


async def upload_evidence(local_path: Path, bitacora_number: int, filename: str) -> Optional[str]:
    """Upload an evidence file to OneDrive under the bitácora folder."""
    folder = settings.onedrive_folder_path.strip("/")
    remote_name = f"Bitacora{bitacora_number}/{filename}"
    return await upload_file(local_path, remote_name)


def is_configured() -> bool:
    return bool(
        settings.onedrive_client_id
        and settings.onedrive_client_secret
        and settings.onedrive_tenant_id
    )
