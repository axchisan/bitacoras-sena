import json
from anthropic import AsyncAnthropic
from app.config import get_settings

settings = get_settings()

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

═══════════════════════════════════════════════════════════
REGLA FUNDAMENTAL: NIVEL DE ABSTRACCIÓN
═══════════════════════════════════════════════════════════

Las descripciones deben hablar del TIPO DE TRABAJO realizado, NO de los detalles específicos de ese trabajo.

Piensa en esto como escribir el perfil de un CV: describes "desarrollé microservicios", no "desarrollé el microservicio ms-polizas-v2 que expone el endpoint /api/novedades/{{id}}".

CRITERIOS para evaluar si una descripción es correcta:
✅ Un instructor SENA que no conoce el proyecto la entiende perfectamente
✅ No revela arquitectura, dominio de negocio ni lógica interna del cliente
✅ Habla de CATEGORÍAS de trabajo: pruebas, desarrollo, análisis, pipelines, etc.
✅ Menciona tecnologías generales: Java, Spring Boot, JUnit, Git, Azure DevOps, etc.

EJEMPLOS CONCRETOS:

❌ MAL: "Se corrigieron bugs en el flujo de creación de novedades y propagación de documentos adjuntos hacia sistemas externos en el microservicio de pólizas"
✅ BIEN: "Se realizó análisis y corrección de errores de funcionalidad en componentes de software de la aplicación, aplicando técnicas de depuración y validación"

❌ MAL: "Se implementaron pruebas unitarias para los casos de uso PolicyApprovalUseCase y NoveltiesProcessorService con JUnit y Mockito"
✅ BIEN: "Se implementaron pruebas unitarias utilizando JUnit y Mockito para incrementar la cobertura de código en los componentes de la aplicación"

❌ MAL: "Se optimizaron los pipelines CI/CD de los repositorios 397-dev-ms-adm-polizas y 397-dev-ms-core-usuarios eliminando etapas duplicadas"
✅ BIEN: "Se optimizaron los pipelines de integración continua en Azure DevOps, reorganizando etapas y eliminando redundancias para mejorar los tiempos de construcción"

❌ MAL: "Se realizó análisis de causa raíz del bug #394543 relacionado con la generación de campos en el archivo CLOB de salida"
✅ BIEN: "Se realizó análisis de causa raíz e implementación de correcciones en componentes del sistema, con posterior creación de pull requests para revisión del equipo"

═══════════════════════════════════════════════════════════

INSTRUCCIONES:
1. Agrupa los work items en actividades coherentes (máximo 6, mínimo 3).
2. Cada actividad debe cubrir entre 2 y 8 días hábiles del período.
3. Cada actividad debe tener:
   - "title": Título general de la categoría de trabajo (máx 80 chars). Ej: "Implementación de pruebas unitarias", "Corrección de errores de funcionalidad", "Optimización de pipelines CI/CD"
   - "description": 2-4 oraciones describiendo el TIPO de actividad y tecnologías generales usadas. Jamás mencionar: nombres de microservicios, módulos, clases, métodos, tablas, endpoints, ni términos del dominio de negocio del cliente (pólizas, novedades, usuarios, etc.). Usar solo términos técnicos genéricos.
   - "competencias": Competencia ADSO directamente relacionada con esta actividad
   - "start_date": Fecha de inicio en YYYY-MM-DD (días hábiles, sin fines de semana)
   - "end_date": Fecha de fin en YYYY-MM-DD (días hábiles, sin fines de semana)
   - "evidence_description": Tipo de evidencia (ej: "Proceso: Implementación de pruebas en repositorio Git", "Entregable: Componentes de software desarrollados", "Producto: Pipeline CI/CD optimizado")
   - "observations": Observaciones adicionales o vacío ""
   - "azure_work_item_ids": IDs de los work items incluidos en esta actividad
4. Usa español formal colombiano.
5. Las fechas deben estar dentro del período indicado, sin fines de semana.

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
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    work_items_summary = []
    for wi in work_items:
        work_items_summary.append({
            "id": wi["azure_id"],
            "title": wi["title"],
            "type": wi["work_item_type"],
            "state": wi["state"],
            "tags": wi.get("tags", ""),
            "changed_date": str(wi.get("changed_date", "")),
        })

    prompt = GENERATION_PROMPT.format(
        competencias_context=SENA_COMPETENCIAS,
        period_label=period_label,
        bitacora_number=bitacora_number,
        work_items_json=json.dumps(work_items_summary, ensure_ascii=False, indent=2),
    )

    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    return _parse_activities(message.content[0].text.strip())


def _parse_activities(response_text: str) -> list[dict]:
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    data = json.loads(response_text)
    activities = data.get("activities", [])
    for i, act in enumerate(activities):
        act["is_ai_generated"] = True
        act["order_index"] = i
    return activities
