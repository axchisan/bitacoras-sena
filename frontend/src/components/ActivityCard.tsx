import { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  updateActivity, uploadEvidence, deleteEvidence,
  getEvidenceUrl, type Activity,
} from "../lib/api";
import { formatDate } from "../lib/utils";
import { Spinner } from "./ui/Spinner";
import {
  Pencil, Trash2, Check, X, Upload, Image,
  CalendarDays, Sparkles, ChevronDown, ChevronUp,
  ExternalLink, FileText,
} from "lucide-react";

interface Props {
  activity: Activity;
  bitacoraId: number;
  onDelete: () => void;
}

export function ActivityCard({ activity, bitacoraId, onDelete }: Props) {
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [form, setForm] = useState({
    title: activity.title,
    description: activity.description,
    competencias: activity.competencias ?? "",
    start_date: activity.start_date ?? "",
    end_date: activity.end_date ?? "",
    evidence_description: activity.evidence_description ?? "",
    observations: activity.observations ?? "",
  });

  const saveMut = useMutation({
    mutationFn: () => updateActivity(activity.id, {
      ...form,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      competencias: form.competencias || null,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bitacora", bitacoraId] });
      setEditing(false);
      toast.success("Actividad guardada");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const uploadMut = useMutation({
    mutationFn: (file: File) => uploadEvidence(activity.id, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bitacora", bitacoraId] });
      toast.success("Evidencia subida");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const deleteEvidMut = useMutation({
    mutationFn: (evidId: number) => deleteEvidence(evidId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bitacora", bitacoraId] });
      toast.success("Evidencia eliminada");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMut.mutate(file);
    e.target.value = "";
  };

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div
        className="flex items-start gap-3 p-4 cursor-pointer hover:bg-gray-800/30 transition-colors"
        onClick={() => !editing && setExpanded(!expanded)}
      >
        {/* Order badge */}
        <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-xs text-gray-500 shrink-0 mt-0.5">
          {activity.order_index + 1}
        </div>

        <div className="flex-1 min-w-0">
          {editing ? (
            <input
              className="field-input font-medium"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <p className="font-medium text-gray-200 text-sm leading-snug">
              {activity.title}
              {activity.is_ai_generated && (
                <Sparkles size={12} className="inline ml-1.5 text-blue-400 opacity-60" />
              )}
            </p>
          )}

          {!editing && (
            <div className="flex items-center gap-3 mt-1 flex-wrap">
              {(activity.start_date || activity.end_date) && (
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <CalendarDays size={11} />
                  {formatDate(activity.start_date)} → {formatDate(activity.end_date)}
                </span>
              )}
              {activity.evidence_files.length > 0 && (
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Image size={11} />
                  {activity.evidence_files.length} evidencia{activity.evidence_files.length > 1 ? "s" : ""}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div
          className="flex items-center gap-1 shrink-0"
          onClick={(e) => e.stopPropagation()}
        >
          {editing ? (
            <>
              <button
                onClick={() => saveMut.mutate()}
                disabled={saveMut.isPending}
                className="btn-primary py-1.5 px-2.5"
              >
                {saveMut.isPending ? <Spinner className="w-3 h-3" /> : <Check size={14} />}
              </button>
              <button
                onClick={() => { setEditing(false); setForm({
                  title: activity.title,
                  description: activity.description,
                  competencias: activity.competencias ?? "",
                  start_date: activity.start_date ?? "",
                  end_date: activity.end_date ?? "",
                  evidence_description: activity.evidence_description ?? "",
                  observations: activity.observations ?? "",
                }); }}
                className="btn-ghost py-1.5 px-2.5"
              >
                <X size={14} />
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => { setEditing(true); setExpanded(true); }}
                className="btn-ghost py-1.5 px-2"
              >
                <Pencil size={14} />
              </button>
              <button
                onClick={() => {
                  if (confirm("¿Eliminar esta actividad?")) onDelete();
                }}
                className="btn-danger py-1.5 px-2"
              >
                <Trash2 size={14} />
              </button>
              <button
                onClick={() => setExpanded(!expanded)}
                className="btn-ghost py-1.5 px-2"
              >
                {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Expanded content */}
      {(expanded || editing) && (
        <div className="px-4 pb-4 pt-1 border-t border-gray-800 space-y-4">
          {/* Description */}
          <div>
            <label className="text-xs font-medium text-gray-400 block mb-1.5">
              Descripción de la actividad
            </label>
            {editing ? (
              <textarea
                className="field-textarea"
                rows={4}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            ) : (
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {activity.description}
              </p>
            )}
          </div>

          {/* Competencias */}
          <div>
            <label className="text-xs font-medium text-gray-400 block mb-1.5">
              Competencias SENA aplicadas
            </label>
            {editing ? (
              <textarea
                className="field-textarea"
                rows={3}
                placeholder="Ej: Construir e implantar componentes de software..."
                value={form.competencias}
                onChange={(e) => setForm({ ...form, competencias: e.target.value })}
              />
            ) : (
              <p className="text-sm text-gray-300 leading-relaxed">
                {activity.competencias || <span className="text-gray-600 italic">Sin competencias definidas</span>}
              </p>
            )}
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-gray-400 block mb-1.5">
                Fecha inicio
              </label>
              {editing ? (
                <input
                  type="date"
                  className="field-input"
                  value={form.start_date}
                  onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                />
              ) : (
                <p className="text-sm text-gray-300">{formatDate(activity.start_date)}</p>
              )}
            </div>
            <div>
              <label className="text-xs font-medium text-gray-400 block mb-1.5">
                Fecha fin
              </label>
              {editing ? (
                <input
                  type="date"
                  className="field-input"
                  value={form.end_date}
                  onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                />
              ) : (
                <p className="text-sm text-gray-300">{formatDate(activity.end_date)}</p>
              )}
            </div>
          </div>

          {/* Evidence description */}
          <div>
            <label className="text-xs font-medium text-gray-400 block mb-1.5">
              Evidencia de cumplimiento
            </label>
            {editing ? (
              <input
                className="field-input"
                placeholder="Ej: Proceso: pruebas unitarias implementadas en repositorio Git"
                value={form.evidence_description}
                onChange={(e) => setForm({ ...form, evidence_description: e.target.value })}
              />
            ) : (
              <p className="text-sm text-gray-300">
                {activity.evidence_description || <span className="text-gray-600 italic">Sin descripción</span>}
              </p>
            )}
          </div>

          {/* Observations */}
          <div>
            <label className="text-xs font-medium text-gray-400 block mb-1.5">
              Observaciones
            </label>
            {editing ? (
              <textarea
                className="field-textarea"
                rows={2}
                placeholder="Observaciones, dificultades, inasistencias..."
                value={form.observations}
                onChange={(e) => setForm({ ...form, observations: e.target.value })}
              />
            ) : (
              <p className="text-sm text-gray-300">
                {activity.observations || <span className="text-gray-600 italic">Sin observaciones</span>}
              </p>
            )}
          </div>

          {/* Evidence files */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-gray-400">
                Archivos de evidencia
              </label>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadMut.isPending}
                className="btn-ghost py-1 px-2 text-xs"
              >
                {uploadMut.isPending ? (
                  <Spinner className="w-3 h-3" />
                ) : (
                  <Upload size={13} />
                )}
                Subir
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.pdf"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>

            {activity.evidence_files.length === 0 ? (
              <div
                className="border-2 border-dashed border-gray-800 rounded-lg p-6 text-center cursor-pointer hover:border-gray-700 transition-colors"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload size={20} className="mx-auto text-gray-600 mb-2" />
                <p className="text-xs text-gray-600">
                  Arrastra o haz clic para subir capturas de pantalla o PDFs
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {activity.evidence_files.map((ev) => (
                  <div key={ev.id} className="relative group rounded-lg overflow-hidden bg-gray-800 border border-gray-700">
                    {ev.file_type.startsWith("image/") ? (
                      <img
                        src={getEvidenceUrl(ev.id)}
                        alt={ev.file_name}
                        className="w-full h-20 object-cover"
                      />
                    ) : (
                      <div className="h-20 flex items-center justify-center">
                        <FileText size={24} className="text-gray-500" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                      <a
                        href={ev.onedrive_url || getEvidenceUrl(ev.id)}
                        target="_blank"
                        rel="noopener"
                        className="p-1.5 rounded bg-white/20 hover:bg-white/30"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink size={13} className="text-white" />
                      </a>
                      <button
                        className="p-1.5 rounded bg-red-600/60 hover:bg-red-600"
                        onClick={() => deleteEvidMut.mutate(ev.id)}
                      >
                        <Trash2 size={13} className="text-white" />
                      </button>
                    </div>
                    <p className="text-[10px] text-gray-500 px-1.5 py-1 truncate">{ev.file_name}</p>
                  </div>
                ))}

                {/* Add more */}
                <div
                  className="h-full min-h-[5rem] border-2 border-dashed border-gray-800 rounded-lg flex items-center justify-center cursor-pointer hover:border-gray-700 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload size={18} className="text-gray-600" />
                </div>
              </div>
            )}
          </div>

          {/* Work Item IDs reference */}
          {activity.azure_work_item_ids && activity.azure_work_item_ids.length > 0 && (
            <div className="flex items-center gap-2 pt-1">
              <span className="text-xs text-gray-600">Work items:</span>
              {activity.azure_work_item_ids.map((wiId) => (
                <a
                  key={wiId}
                  href={`https://dev.azure.com/linktic/${encodeURIComponent("397 - COLFONDOS CORE")}/_workitems/edit/${wiId}`}
                  target="_blank"
                  rel="noopener"
                  className="text-xs text-blue-500 hover:text-blue-400 flex items-center gap-0.5"
                >
                  #{wiId} <ExternalLink size={10} />
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
