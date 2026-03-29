import json
from anthropic import AsyncAnthropic
from app.config import get_settings

settings = get_settings()

# Competencias ADSO del programa Tecnólogo en Análisis y Desarrollo de Software
SENA_COMPETENCIAS = """
Las competencias del programa 'Tecnólogo en Análisis y Desarrollo de Software' (ADSO) son:
1. Gestionar la infraestructura tecnológica requerida en el proceso de desarrollo de software
2. Aplicar el modelo de programación orientado a objetos según requerimientos del proyecto de software
3. Construir e implantar componentes de software utilizando metodologías de desarrollo
4. Gestionar bases de datos relacionales y no relacionales aplicando lenguaje de consulta estructurado
5. Analizar los requerimientos según metodologías establecidas para el desarrollo del software
6. Aplicar herramientas de control de versiones en el desarrollo colaborativo de software
7. Implementar pruebas de software que garanticen la calidad del producto
8. Documentar el proceso de desarrollo de software según estándares y metodologías
9. Gestionar el proceso de desarrollo de software utilizando metodologías ágiles (Scrum, Kanban)
10. Aplicar principios de seguridad en el desarrollo de aplicaciones
"""

GENERATION_PROMPT = """Eres un asistente experto en documentación SENA para la Etapa Productiva del programa Tecnólogo en Análisis y Desarrollo de Software (ADSO).

Tu tarea es generar el contenido de una bitácora de seguimiento a partir de los work items (tareas) de Azure DevOps que el aprendiz realizó durante un período específico.

{competencias_context}

PERÍODO: {period_label}
BITÁCORA N°: {bitacora_number}

WORK ITEMS DEL PERÍODO:
{work_items_json}

INSTRUCCIONES:
1. Agrupa los work items en actividades coherentes (máximo 6 actividades, mínimo 3).
2. Cada actividad debe tener:
   - "title": Título conciso y profesional de la actividad (máx 80 chars)
   - "description": Descripción formal detallada de la actividad (2-4 oraciones), redactada en tercera persona o infinitivo, en tono técnico-profesional apropiado para un documento SENA. Debe detallar QUÉ se hizo, CÓMO y con qué herramientas/tecnologías.
   - "competencias": Una o dos competencias del programa ADSO que aplican directamente a esta actividad. Redactar de forma precisa y relacionada con la actividad específica.
   - "start_date": Fecha de inicio estimada en formato YYYY-MM-DD (dentro del período)
   - "end_date": Fecha de fin estimada en formato YYYY-MM-DD (dentro del período)
   - "evidence_description": Qué tipo de evidencia existe (ej: "Proceso: Implementación de pruebas unitarias en repositorio Git", "Entregable: Módulo de microservicio desarrollado y mergeado")
   - "observations": Observaciones relevantes si aplica (puede ser vacío "")
   - "azure_work_item_ids": Lista de IDs de los work items agrupados en esta actividad

3. La descripción debe sonar profesional y técnica, apta para presentar ante un instructor SENA.
4. Usa lenguaje en español formal colombiano.
5. Los fines de semana no cuentan como días de trabajo, tenlo en cuenta para las fechas.

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "activities": [
    {{
      "title": "...",
      "description": "...",
      "competencias": "...",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "evidence_description": "...",
      "observations": "",
      "azure_work_item_ids": [123, 456]
    }}
  ]
}}
"""


async def generate_bitacora_activities(
    bitacora_number: int,
    period_label: str,
    work_items: list[dict],
) -> list[dict]:
    """
    Uses Claude to generate structured activities from Azure DevOps work items.
    Returns a list of activity dicts ready to be saved to the database.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    work_items_summary = []
    for wi in work_items:
        work_items_summary.append({
            "id": wi["azure_id"],
            "title": wi["title"],
            "description": wi.get("description", "")[:500],
            "type": wi["work_item_type"],
            "state": wi["state"],
            "tags": wi.get("tags", ""),
            "changed_date": str(wi.get("changed_date", "")),
            "closed_date": str(wi.get("closed_date", "")),
        })

    prompt = GENERATION_PROMPT.format(
        competencias_context=SENA_COMPETENCIAS,
        period_label=period_label,
        bitacora_number=bitacora_number,
        work_items_json=json.dumps(work_items_summary, ensure_ascii=False, indent=2),
    )

    message = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    # Extract JSON from response (handle potential markdown code blocks)
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    data = json.loads(response_text)
    activities = data.get("activities", [])

    # Add metadata flag
    for i, act in enumerate(activities):
        act["is_ai_generated"] = True
        act["order_index"] = i

    return activities
