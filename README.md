# Bitácoras SENA — Sistema de Automatización

Sistema web para generar automáticamente las bitácoras de seguimiento de etapa productiva SENA, integrando Azure DevOps + Claude AI + OneDrive.

## ¿Qué hace?

Consulta las tareas (work items) de Azure DevOps en un rango de fechas, usa IA (Claude) para generar descripciones profesionales y competencias SENA, y produce el Excel oficial listo para entregar al instructor, todo desde una interfaz web sin tocar Excel.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python · FastAPI · SQLAlchemy async |
| Base de datos | PostgreSQL 16 |
| IA | Anthropic Claude (claude-opus-4-6) |
| Excel | openpyxl |
| Azure DevOps | REST API (WIQL) |
| OneDrive | Microsoft Graph API |
| Frontend | React · Vite · Tailwind CSS · React Query |
| Deploy | Docker · Coolify |

## Estructura

```
bitacoras-sena/
├── backend/
│   └── app/
│       ├── main.py               # FastAPI app
│       ├── config.py             # Settings desde variables de entorno
│       ├── database.py           # Conexión PostgreSQL async
│       ├── models/               # SQLAlchemy models
│       ├── schemas/              # Pydantic schemas
│       ├── services/
│       │   ├── azure_devops.py   # Consulta work items por fecha
│       │   ├── claude_service.py # Generación de actividades con IA
│       │   ├── excel_service.py  # Llenado del Excel con openpyxl
│       │   └── onedrive_service.py
│       ├── routers/              # Endpoints REST
│       └── utils/dates.py        # Cálculo automático de los 12 períodos
├── frontend/
│   └── src/
│       ├── pages/                # Dashboard · Bitácoras · WorkItems · Settings
│       └── components/           # ActivityCard · WorkItemsPanel · Sidebar
├── nginx/nginx.conf              # Reverse proxy
├── templates/bitacora_base.xlsx  # Plantilla Excel oficial SENA
├── docker-compose.yml
└── .env.example
```

## Variables de entorno

Copia `.env.example` como `.env` para desarrollo local. En producción configura cada variable en Coolify UI — nunca se exponen en el repo.

| Variable | Descripción |
|---|---|
| `POSTGRES_PASSWORD` | Contraseña de la base de datos |
| `AZURE_DEVOPS_ORG` | Organización en Azure DevOps (`linktic`) |
| `AZURE_DEVOPS_PROJECT` | Nombre del proyecto (`397 - COLFONDOS CORE`) |
| `AZURE_DEVOPS_PAT` | Personal Access Token — scope: Work Items · Read |
| `ANTHROPIC_API_KEY` | API Key de Anthropic (console.anthropic.com) |
| `ONEDRIVE_CLIENT_ID` | App ID registrada en Azure Portal |
| `ONEDRIVE_CLIENT_SECRET` | Client secret value (no el ID) |
| `ONEDRIVE_TENANT_ID` | Tenant ID de la cuenta Microsoft |
| `ONEDRIVE_FOLDER_PATH` | Carpeta destino en OneDrive (ej: `/Bitacoras SENA`) |
| `SECRET_KEY` | Clave aleatoria para firmado interno |
| `ENVIRONMENT` | `development` o `production` |
| `CORS_ORIGINS` | Orígenes permitidos (ej: `https://bitacoras.axchisan.com`) |
| `NGINX_PORT` | Puerto local del nginx (default: `8080`) |
| `BITACORAS_START_DATE` | Fecha inicio etapa productiva (`2026-01-26`) |
| `BITACORAS_TOTAL` | Total de bitácoras (`12`) |
| `BITACORAS_PERIOD_DAYS` | Días por período (`15`) |

### Obtener el PAT de Azure DevOps
1. Entra a `dev.azure.com/linktic` → tu avatar → **Personal access tokens**
2. **New Token** · Scope: `Work Items → Read` · Expiración: 1 año

### Obtener credenciales de OneDrive
1. `portal.azure.com` → **App registrations** → **New registration**
2. Supported account types: `Any Entra ID Tenant + Personal Microsoft accounts`
3. Copia **Application (client) ID** → `ONEDRIVE_CLIENT_ID`
4. **Certificates & secrets** → **New client secret** → copia el **Value** → `ONEDRIVE_CLIENT_SECRET`
5. Copia **Directory (tenant) ID** → `ONEDRIVE_TENANT_ID`
6. **API permissions** → Add → Microsoft Graph → Delegated → `Files.ReadWrite`

> OneDrive es opcional. Sin configurarlo, la app funciona igual y el botón de subida queda desactivado.

## Desarrollo local

```bash
# 1. Clona el repo
git clone https://github.com/axchisan/bitacoras-sena.git
cd bitacoras-sena

# 2. Configura el entorno
cp .env.example .env
# Edita .env con tus credenciales

# 3. Levanta todos los servicios
docker compose up --build

# 4. Abre en el navegador
# http://localhost:8080
```

Para ver logs en tiempo real:
```bash
docker compose logs -f backend   # errores de API
docker compose logs -f postgres  # base de datos
```

Para parar:
```bash
docker compose down
```

## Producción (Coolify)

1. En Coolify → **New Resource** → **Docker Compose**
2. Conecta el repo `axchisan/bitacoras-sena` · branch `main`
3. Agrega todas las variables de entorno en la UI de Coolify
4. Configura el dominio `bitacoras.axchisan.com`
5. Agrega el registro DNS: `A · bitacoras · 147.93.178.204`
6. Deploy — Coolify maneja el build, SSL y proxy automáticamente

## Flujo de uso

```
1. Abrir el Dashboard
   → Ver las 12 bitácoras con su estado y fechas

2. Seleccionar una bitácora pendiente
   → Expandir los Work Items del período (viene de Azure DevOps)
   → Opcionalmente seleccionar solo algunos items específicos

3. Generar con IA
   → Claude analiza los work items y genera actividades
     con descripciones formales y competencias SENA

4. Revisar y editar
   → Editar cualquier campo inline en la interfaz
   → Subir capturas de pantalla como evidencia

5. Exportar
   → Descarga el Excel oficial ya diligenciado
   → (Opcional) Subir automáticamente a OneDrive
```

## Períodos de bitácoras

| N° | Desde | Hasta | Entrega |
|---|---|---|---|
| 1 | 26/01/2026 | 09/02/2026 | 14/02/2026 |
| 2 | 10/02/2026 | 24/02/2026 | 01/03/2026 |
| 3 | 25/02/2026 | 11/03/2026 | 16/03/2026 |
| 4 | 12/03/2026 | 26/03/2026 | 31/03/2026 |
| 5 | 27/03/2026 | 10/04/2026 | 15/04/2026 |
| 6 | 11/04/2026 | 25/04/2026 | 30/04/2026 |
| 7 | 26/04/2026 | 10/05/2026 | 15/05/2026 |
| 8 | 11/05/2026 | 25/05/2026 | 30/05/2026 |
| 9 | 26/05/2026 | 09/06/2026 | 14/06/2026 |
| 10 | 10/06/2026 | 24/06/2026 | 29/06/2026 |
| 11 | 25/06/2026 | 09/07/2026 | 14/07/2026 |
| 12 | 10/07/2026 | 24/07/2026 | 29/07/2026 |
