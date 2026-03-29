import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  getBitacora, generateBitacora, exportBitacora, uploadToOneDrive,
  deleteActivity, getWorkItemsForBitacora, updateBitacora,
} from "../lib/api";
import { formatDate } from "../lib/utils";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Spinner } from "../components/ui/Spinner";
import { ActivityCard } from "../components/ActivityCard";
import { WorkItemsPanel } from "../components/WorkItemsPanel";
import {
  Sparkles, Download, Upload, ArrowLeft, RefreshCw,
  CalendarDays, ExternalLink, ChevronDown, ChevronUp, Terminal, X,
} from "lucide-react";

export default function BitacoraDetail() {
  const { id } = useParams<{ id: string }>();
  const bitacoraId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [showWorkItems, setShowWorkItems] = useState(false);
  const [selectedWorkItems, setSelectedWorkItems] = useState<number[]>([]);
  const [regenerate, setRegenerate] = useState(false);
  const [showClaudeModal, setShowClaudeModal] = useState(false);

  const { data: bitacora, isLoading } = useQuery({
    queryKey: ["bitacora", bitacoraId],
    queryFn: () => getBitacora(bitacoraId),
  });

  const { data: workItems, isFetching: loadingWI } = useQuery({
    queryKey: ["work-items", bitacoraId],
    queryFn: () => getWorkItemsForBitacora(bitacoraId),
    enabled: showWorkItems,
  });

  const generateMut = useMutation({
    mutationFn: () =>
      generateBitacora(
        bitacoraId,
        selectedWorkItems.length > 0 ? selectedWorkItems : undefined,
        regenerate
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bitacora", bitacoraId] });
      qc.invalidateQueries({ queryKey: ["bitacoras"] });
      toast.success("¡Actividades generadas con IA!");
      setRegenerate(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const exportMut = useMutation({
    mutationFn: () => exportBitacora(bitacoraId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bitacora", bitacoraId] });
      qc.invalidateQueries({ queryKey: ["bitacoras"] });
      toast.success("Excel generado");
      window.open(`/api/bitacoras/${bitacoraId}/download`, "_blank");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const oneDriveMut = useMutation({
    mutationFn: () => uploadToOneDrive(bitacoraId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bitacora", bitacoraId] });
      qc.invalidateQueries({ queryKey: ["bitacoras"] });
      toast.success("Subida a OneDrive exitosamente");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const deleteActivityMut = useMutation({
    mutationFn: (actId: number) => deleteActivity(actId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bitacora", bitacoraId] });
      qc.invalidateQueries({ queryKey: ["bitacoras"] });
      toast.success("Actividad eliminada");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const markReadyMut = useMutation({
    mutationFn: () => updateBitacora(bitacoraId, { status: "ready" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bitacora", bitacoraId] });
      qc.invalidateQueries({ queryKey: ["bitacoras"] });
      toast.success("Marcada como lista");
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner className="w-8 h-8" />
      </div>
    );
  }
  if (!bitacora) return <p className="text-gray-500">Bitácora no encontrada</p>;

  const hasActivities = bitacora.activities.length > 0;
  const isGenerating = generateMut.isPending;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <button onClick={() => navigate(-1)} className="btn-ghost mt-0.5">
          <ArrowLeft size={16} />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-100">
              Bitácora {bitacora.number}
            </h1>
            <StatusBadge status={bitacora.status} />
          </div>
          <p className="text-gray-500 text-sm mt-1 flex items-center gap-2">
            <CalendarDays size={13} />
            {formatDate(bitacora.period_start)} → {formatDate(bitacora.period_end)}
            {bitacora.delivery_date && (
              <span className="text-gray-600">
                · Entrega: {formatDate(bitacora.delivery_date)}
              </span>
            )}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {bitacora.onedrive_url && (
            <a href={bitacora.onedrive_url} target="_blank" rel="noopener" className="btn-ghost text-xs">
              <ExternalLink size={14} /> OneDrive
            </a>
          )}

          {hasActivities && bitacora.status === "draft" && (
            <button onClick={() => markReadyMut.mutate()} className="btn-secondary">
              Marcar lista
            </button>
          )}

          {hasActivities && (
            <>
              <button
                onClick={() => exportMut.mutate()}
                disabled={exportMut.isPending}
                className="btn-secondary"
              >
                {exportMut.isPending ? <Spinner className="w-4 h-4" /> : <Download size={16} />}
                Exportar Excel
              </button>
              <button
                onClick={() => oneDriveMut.mutate()}
                disabled={oneDriveMut.isPending || !bitacora.excel_file_path}
                className="btn-secondary"
              >
                {oneDriveMut.isPending ? <Spinner className="w-4 h-4" /> : <Upload size={16} />}
                OneDrive
              </button>
            </>
          )}

          <button
            onClick={() => setShowClaudeModal(true)}
            className="btn-secondary"
            title="Generar usando Claude Code (sin créditos de API)"
          >
            <Terminal size={16} />
            Claude Code
          </button>

          <button
            onClick={() => {
              if (hasActivities) setRegenerate(true);
              generateMut.mutate();
            }}
            disabled={isGenerating}
            className="btn-primary"
          >
            {isGenerating ? (
              <><Spinner className="w-4 h-4" /> Generando...</>
            ) : (
              <><Sparkles size={16} /> {hasActivities ? "Regenerar con IA" : "Generar con IA"}</>
            )}
          </button>
        </div>
      </div>

      {/* Work Items toggle */}
      <div className="card overflow-hidden">
        <button
          onClick={() => setShowWorkItems(!showWorkItems)}
          className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-gray-800/50 transition-colors"
        >
          <span className="text-sm font-medium text-gray-300 flex items-center gap-2">
            <RefreshCw size={15} className="text-blue-400" />
            Work Items del período
            {workItems && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400">
                {workItems.length}
              </span>
            )}
          </span>
          {showWorkItems ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
        </button>

        {showWorkItems && (
          <div className="border-t border-gray-800">
            <WorkItemsPanel
              workItems={workItems ?? []}
              loading={loadingWI}
              selected={selectedWorkItems}
              onSelect={setSelectedWorkItems}
            />
          </div>
        )}
      </div>

      {/* Generating state */}
      {isGenerating && (
        <div className="card p-8 flex flex-col items-center gap-4">
          <Spinner className="w-10 h-10" />
          <div className="text-center">
            <p className="font-medium text-gray-200">Generando actividades con IA...</p>
            <p className="text-sm text-gray-500 mt-1">
              Claude está analizando tus work items para crear la bitácora
            </p>
          </div>
        </div>
      )}

      {/* Modal: Claude Code */}
      {showClaudeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <Terminal size={18} className="text-green-400" />
                <span className="font-semibold text-gray-100">Generar via Claude Code</span>
              </div>
              <button onClick={() => setShowClaudeModal(false)} className="btn-ghost p-1">
                <X size={16} />
              </button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <p className="text-sm text-gray-400">
                Usa esta opción cuando no tengas créditos en la API de Claude.
                Claude Code (el CLI) genera las actividades usando tu plan Pro.
              </p>
              <div className="bg-gray-800 rounded-lg px-4 py-3 space-y-1">
                <p className="text-xs text-gray-500 mb-2">Dile esto a Claude Code en tu terminal:</p>
                <code className="text-green-400 text-sm font-mono block">
                  genera la bitácora {bitacora.number}
                </code>
              </div>
              <div className="text-xs text-gray-600 space-y-1">
                <p>• Claude Code consultará los work items de Azure DevOps</p>
                <p>• Generará las actividades y las publicará directamente en la app</p>
                <p>• La página se actualizará automáticamente al terminar</p>
              </div>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(`genera la bitácora ${bitacora.number}`);
                  toast.success("Comando copiado al portapapeles");
                }}
                className="btn-secondary w-full text-sm"
              >
                Copiar comando
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Activities */}
      {!isGenerating && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-100">
              Actividades
              {hasActivities && (
                <span className="ml-2 text-sm text-gray-500 font-normal">
                  ({bitacora.activities.length})
                </span>
              )}
            </h2>
          </div>

          {!hasActivities ? (
            <div className="card p-12 flex flex-col items-center gap-4 text-center">
              <div className="w-12 h-12 rounded-full bg-gray-800 flex items-center justify-center">
                <Sparkles size={24} className="text-gray-600" />
              </div>
              <div>
                <p className="font-medium text-gray-300">Sin actividades aún</p>
                <p className="text-sm text-gray-600 mt-1">
                  Haz clic en "Generar con IA" para crear las actividades automáticamente
                  desde tus work items de Azure DevOps
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {[...bitacora.activities]
                .sort((a, b) => a.order_index - b.order_index)
                .map((activity) => (
                  <ActivityCard
                    key={activity.id}
                    activity={activity}
                    bitacoraId={bitacoraId}
                    onDelete={() => deleteActivityMut.mutate(activity.id)}
                  />
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
