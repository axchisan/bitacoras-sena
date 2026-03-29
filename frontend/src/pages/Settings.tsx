import { useQuery } from "@tanstack/react-query";
import { getConfig } from "../lib/api";
import { CheckCircle2, XCircle, ExternalLink } from "lucide-react";

export default function Settings() {
  const { data: config } = useQuery({ queryKey: ["config"], queryFn: getConfig });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Configuración</h1>
        <p className="text-gray-500 text-sm mt-1">Estado del sistema y credenciales</p>
      </div>

      {/* Integration status */}
      <div className="card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-gray-300">Integraciones</h2>
        <div className="space-y-3">
          <IntegrationRow
            label="Azure DevOps"
            sub="linktic · 397 - COLFONDOS CORE"
            active={true}
          />
          <IntegrationRow
            label="Anthropic Claude"
            sub="claude-opus-4-6 · Generación de actividades"
            active={true}
          />
          <IntegrationRow
            label="OneDrive / Microsoft Graph"
            sub={config?.onedrive_configured ? "Carpeta configurada" : "No configurado — agrega credenciales en .env"}
            active={config?.onedrive_configured ?? false}
          />
        </div>
      </div>

      {/* Períodos */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-gray-300 mb-4">Períodos de bitácoras</h2>
        <div className="space-y-1.5">
          {config?.periods.map((p) => (
            <div
              key={p.number}
              className={`flex items-center justify-between py-2 px-3 rounded-lg text-sm ${
                p.number === config.current_bitacora
                  ? "bg-blue-900/20 border border-blue-800/50"
                  : "hover:bg-gray-800/50"
              }`}
            >
              <span className="text-gray-300">
                <span className="font-mono text-gray-500 text-xs mr-2">#{p.number}</span>
                {p.label}
              </span>
              <span className="text-xs text-gray-600">
                Entrega: {p.delivery_date}
                {p.number === config.current_bitacora && (
                  <span className="ml-2 text-blue-400 font-medium">← Actual</span>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Help */}
      <div className="card p-5 space-y-3">
        <h2 className="text-sm font-semibold text-gray-300">Configuración de OneDrive</h2>
        <p className="text-sm text-gray-500">
          Para habilitar la subida automática a OneDrive, registra una app en Azure Portal y agrega las credenciales al archivo <code className="text-blue-400 bg-gray-800 px-1 rounded">.env</code>:
        </p>
        <div className="bg-gray-800 rounded-lg p-3 font-mono text-xs text-gray-300 space-y-1">
          <p>ONEDRIVE_CLIENT_ID=...</p>
          <p>ONEDRIVE_CLIENT_SECRET=...</p>
          <p>ONEDRIVE_TENANT_ID=...</p>
          <p>ONEDRIVE_FOLDER_PATH=/Bitacoras SENA</p>
        </div>
        <a
          href="https://portal.azure.com"
          target="_blank"
          rel="noopener"
          className="btn-ghost text-xs"
        >
          <ExternalLink size={13} /> Abrir Azure Portal
        </a>
      </div>
    </div>
  );
}

function IntegrationRow({
  label, sub, active,
}: { label: string; sub: string; active: boolean }) {
  return (
    <div className="flex items-center gap-3 py-2">
      {active ? (
        <CheckCircle2 size={16} className="text-green-400 shrink-0" />
      ) : (
        <XCircle size={16} className="text-gray-600 shrink-0" />
      )}
      <div>
        <p className="text-sm font-medium text-gray-200">{label}</p>
        <p className="text-xs text-gray-500">{sub}</p>
      </div>
    </div>
  );
}
