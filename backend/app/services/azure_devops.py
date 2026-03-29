from datetime import date, datetime, timezone
from typing import Optional
import httpx
import base64
from app.config import get_settings

settings = get_settings()


def _get_auth_header() -> dict:
    token = base64.b64encode(f":{settings.azure_devops_pat}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def _base_url() -> str:
    return f"https://dev.azure.com/{settings.azure_devops_org}"


async def fetch_work_items_by_date_range(
    start: date,
    end: date,
    assigned_to_me: bool = True,
) -> list[dict]:
    """
    Query Azure DevOps WIQL for work items created/modified in a date range.
    Returns raw work item dicts with all relevant fields.
    """
    # Azure DevOps WIQL only accepts date format, not datetime/timestamps
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    project = settings.azure_devops_project

    # Build WIQL — filter by project name string to avoid URL encoding issues
    assigned_clause = "[System.AssignedTo] = @Me AND" if assigned_to_me else ""
    wiql = {
        "query": (
            f"SELECT [System.Id] FROM WorkItems "
            f"WHERE {assigned_clause} "
            f"[System.TeamProject] = '{project}' "
            f"AND [System.WorkItemType] IN ('Task', 'User Story', 'Bug', 'Feature') "
            f"AND [System.ChangedDate] >= '{start_str}' "
            f"AND [System.ChangedDate] <= '{end_str}' "
            f"ORDER BY [System.ChangedDate] DESC"
        )
    }

    # Use org-level endpoint — avoids project name URL encoding issues
    url = f"{_base_url()}/_apis/wit/wiql?api-version=7.1"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=wiql, headers=_get_auth_header())
        if not resp.is_success:
            raise Exception(
                f"Azure DevOps WIQL error {resp.status_code}: {resp.text[:300]}"
            )
        data = resp.json()

    work_item_refs = data.get("workItems", [])
    if not work_item_refs:
        return []

    ids = [wi["id"] for wi in work_item_refs[:50]]
    return await fetch_work_items_by_ids(ids)


async def fetch_work_items_by_ids(ids: list[int]) -> list[dict]:
    if not ids:
        return []

    fields = [
        "System.Id",
        "System.Title",
        "System.Description",
        "System.WorkItemType",
        "System.State",
        "System.AssignedTo",
        "System.AreaPath",
        "System.IterationPath",
        "System.Tags",
        "System.CreatedDate",
        "System.ChangedDate",
        "Microsoft.VSTS.Common.ClosedDate",
        "Microsoft.VSTS.Scheduling.CompletedWork",
        "Microsoft.VSTS.Scheduling.OriginalEstimate",
    ]

    # workitemsbatch is org-level — no project in URL needed
    url = f"{_base_url()}/_apis/wit/workitemsbatch?api-version=7.1"
    payload = {"ids": ids[:200], "fields": fields}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=_get_auth_header())
        if not resp.is_success:
            raise Exception(
                f"Azure DevOps batch error {resp.status_code}: {resp.text[:300]}"
            )
        data = resp.json()

    return [_parse_work_item(wi) for wi in data.get("value", [])]


def _parse_date(value: str | None) -> datetime | None:
    """Parse ISO 8601 date strings from Azure DevOps into datetime objects."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        # Handle formats like '2026-02-02T17:24:38.26Z' or '2026-02-02T17:24:38.813Z'
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_work_item(raw: dict) -> dict:
    fields = raw.get("fields", {})
    assigned_to = fields.get("System.AssignedTo", {})
    if isinstance(assigned_to, dict):
        assigned_to = assigned_to.get("displayName", "")

    return {
        "azure_id": raw["id"],
        "title": fields.get("System.Title", ""),
        "description": _strip_html(fields.get("System.Description") or ""),
        "work_item_type": fields.get("System.WorkItemType", ""),
        "state": fields.get("System.State", ""),
        "assigned_to": assigned_to,
        "area_path": fields.get("System.AreaPath", ""),
        "iteration_path": fields.get("System.IterationPath", ""),
        "tags": fields.get("System.Tags", ""),
        "completed_work": fields.get("Microsoft.VSTS.Scheduling.CompletedWork"),
        "original_estimate": fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate"),
        "created_date": _parse_date(fields.get("System.CreatedDate")),
        "changed_date": _parse_date(fields.get("System.ChangedDate")),
        "closed_date": _parse_date(fields.get("Microsoft.VSTS.Common.ClosedDate")),
        "url": f"https://dev.azure.com/{settings.azure_devops_org}/"
               f"{settings.azure_devops_project}/_workitems/edit/{raw['id']}",
    }


def _strip_html(text: str) -> str:
    import re
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


async def get_current_user_email() -> Optional[str]:
    """Get the email/display name of the authenticated user."""
    url = f"https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=7.1"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=_get_auth_header())
        if resp.status_code == 200:
            data = resp.json()
            return data.get("emailAddress") or data.get("displayName")
    return None
