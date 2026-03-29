import { cn, WORK_ITEM_TYPE_COLOR } from "../lib/utils";
import { Spinner } from "./ui/Spinner";
import type { WorkItem } from "../lib/api";
import { ExternalLink, CheckSquare, Square } from "lucide-react";
import { formatDate } from "../lib/utils";

interface Props {
  workItems: WorkItem[];
  loading: boolean;
  selected: number[];
  onSelect: (ids: number[]) => void;
}

export function WorkItemsPanel({ workItems, loading, selected, onSelect }: Props) {
  const toggle = (id: number) => {
    if (selected.includes(id)) {
      onSelect(selected.filter((s) => s !== id));
    } else {
      onSelect([...selected, id]);
    }
  };

  const toggleAll = () => {
    if (selected.length === workItems.length) {
      onSelect([]);
    } else {
      onSelect(workItems.map((w) => w.azure_id));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8 gap-3">
        <Spinner />
        <span className="text-sm text-gray-500">Consultando Azure DevOps...</span>
      </div>
    );
  }

  if (workItems.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-gray-500">
        No se encontraron work items en este período
      </div>
    );
  }

  return (
    <div>
      {/* Select all */}
      <div className="px-4 py-2.5 border-b border-gray-800 flex items-center justify-between">
        <button
          onClick={toggleAll}
          className="text-xs text-gray-400 hover:text-gray-200 flex items-center gap-1.5 transition-colors"
        >
          {selected.length === workItems.length ? (
            <CheckSquare size={14} className="text-blue-400" />
          ) : (
            <Square size={14} />
          )}
          {selected.length === 0
            ? "Seleccionar todos"
            : selected.length === workItems.length
            ? "Deseleccionar todos"
            : `${selected.length} seleccionados`}
        </button>
        {selected.length > 0 && (
          <span className="text-xs text-blue-400">
            La IA usará solo los seleccionados
          </span>
        )}
      </div>

      {/* Items list */}
      <div className="divide-y divide-gray-800 max-h-72 overflow-y-auto">
        {workItems.map((wi) => {
          const isSelected = selected.includes(wi.azure_id);
          const typeColor = WORK_ITEM_TYPE_COLOR[wi.work_item_type] ?? "text-gray-400 bg-gray-800";

          return (
            <div
              key={wi.azure_id}
              className={cn(
                "flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-gray-800/50 transition-colors",
                isSelected && "bg-blue-900/10"
              )}
              onClick={() => toggle(wi.azure_id)}
            >
              <div className="mt-0.5 shrink-0">
                {isSelected ? (
                  <CheckSquare size={15} className="text-blue-400" />
                ) : (
                  <Square size={15} className="text-gray-600" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={cn("text-[10px] px-1.5 py-0.5 rounded font-medium", typeColor)}>
                    {wi.work_item_type}
                  </span>
                  <span className="text-xs text-gray-400 font-mono">#{wi.azure_id}</span>
                  <span className="text-xs text-gray-500">{wi.state}</span>
                </div>
                <p className="text-sm text-gray-200 mt-0.5 leading-snug line-clamp-2">{wi.title}</p>
                {(wi.changed_date || wi.closed_date) && (
                  <p className="text-xs text-gray-600 mt-0.5">
                    {wi.closed_date
                      ? `Cerrado: ${formatDate(wi.closed_date)}`
                      : `Modificado: ${formatDate(wi.changed_date)}`}
                  </p>
                )}
              </div>

              {wi.url && (
                <a
                  href={wi.url}
                  target="_blank"
                  rel="noopener"
                  className="shrink-0 text-gray-600 hover:text-blue-400 transition-colors mt-0.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink size={13} />
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
