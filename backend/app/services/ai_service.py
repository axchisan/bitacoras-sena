"""
Servicio unificado de IA para generación de actividades de bitácoras.
Soporta múltiples proveedores: Anthropic Claude, Google Gemini, Groq (Llama).
"""
import json
import httpx
from app.config import get_settings
from app.services.claude_service import GENERATION_PROMPT, SENA_COMPETENCIAS, _parse_activities

settings = get_settings()


async def generate_bitacora_activities(
    bitacora_number: int,
    period_label: str,
    work_items: list[dict],
    provider: str | None = None,
) -> list[dict]:
    """
    Genera actividades usando el proveedor especificado (o el configurado por defecto).
    provider: 'anthropic' | 'gemini' | 'groq'
    """
    active_provider = provider or settings.ai_provider

    work_items_summary = [
        {
            "id": wi["azure_id"],
            "title": wi["title"],
            "type": wi["work_item_type"],
            "state": wi["state"],
            "tags": wi.get("tags", ""),
            "changed_date": str(wi.get("changed_date", "")),
        }
        for wi in work_items
    ]

    prompt = GENERATION_PROMPT.format(
        competencias_context=SENA_COMPETENCIAS,
        period_label=period_label,
        bitacora_number=bitacora_number,
        work_items_json=json.dumps(work_items_summary, ensure_ascii=False, indent=2),
    )

    if active_provider == "gemini":
        response_text = await _call_gemini(prompt)
    elif active_provider == "groq":
        response_text = await _call_groq(prompt)
    else:
        # Default: Anthropic Claude
        from app.services import claude_service
        return await claude_service.generate_bitacora_activities(
            bitacora_number=bitacora_number,
            period_label=period_label,
            work_items=work_items,
        )

    return _parse_activities(response_text)


async def _call_gemini(prompt: str) -> str:
    """Google Gemini 1.5 Flash — free tier: 15 RPM, 1M tokens/día."""
    api_key = settings.gemini_api_key
    if not api_key:
        raise ValueError("GEMINI_API_KEY no está configurado")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 4096,
            "temperature": 0.3,
            "responseMimeType": "application/json",
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            raise Exception(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


async def _call_groq(prompt: str) -> str:
    """Groq + Llama 3.3 70B — free tier: 500K tokens/día, muy rápido."""
    api_key = settings.groq_api_key
    if not api_key:
        raise ValueError("GROQ_API_KEY no está configurado")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
        )
        if resp.status_code != 200:
            raise Exception(f"Groq API error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()

    return data["choices"][0]["message"]["content"]
