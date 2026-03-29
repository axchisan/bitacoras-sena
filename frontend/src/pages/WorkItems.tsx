import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getWorkItems, syncWorkItems, getBitacoras } from "../lib/api";
import { WORK_ITEM_TYPE_COLOR, formatDate } from "../lib/utils";
import { Spinner } from "../components/ui/Spinner";
import { cn } from "../lib/utils";
import { RefreshCw, ExternalLink, Search } from "lucide-react";
import toast from "react-hot-toast";

export default function WorkItems() {
  const qc = useQueryClient();
  const { data: bitacoras } = useQuery({ queryKey: ["bitacoras"], queryFn: getBitacoras });

  const [selectedBitacora, setSelectedBitacora] = useState<string>("1");
  const [search, setSearch] = useState("");

  const period = bitacoras?.find((b) => b.number === Number(selectedBitacora));
  const startDate = period?.period_start ?? "";
  const endDate = period?.period_end ?? "";

  const { data: workItems, isLoading } = useQuery({
    queryKey: ["work-items-page", startDate, endDate],
    queryFn: () => getWorkItems(startDate, endDate),
    enabled: !!startDate && !!endDate,
  });

  const syncMut = useMutation({
    mutationFn: () => syncWorkItems(startDate, endDate),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["work-items-page", startDate, endDate] });
      toast.success(`${data.count} work items sincronizados`);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const filtered = workItems?.filter((w) =>
    search === "" ||
    w.title.toLowerCase().includes(search.toLowerCase()) ||
    String(w.azure_id).includes(search)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Work Items</h1>
          <p className="text-gray-500 text-sm mt-1">Consulta tus tareas de Azure DevOps por período</p>
        </div>
        <button
          onClick={() => syncMut.mutate()}
          disabled={syncMut.isPending || !startDate}
          className="btn-secondary"
        >
          {syncMut.isPending ? <Spinner className="w-4 h-4" /> : <RefreshCw size={15} />}
          Sincronizar
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <select
          value={selectedBitacora}
          onChange={(e) => setSelectedBitacora(e.target.value)}
          className="field-input max-w-xs"
        >
          {bitacoras?.map((b) => (
            <option key={b.number} value={b.number}>
              Bitácora {b.number} · {formatDate(b.period_start)} → {formatDate(b.period_end)}
            </option>
          ))}
        </select>

        <div className="relative flex-1 max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            className="field-input pl-9"
            placeholder="Buscar por título o ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12 gap-3">
            <Spinner />
            <span className="text-sm text-gray-500">Consultando Azure DevOps...</span>
          </div>
        ) : !filtered?.length ? (
          <div className="py-12 text-center text-sm text-gray-500">
            No se encontraron work items para este período
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 w-16">#ID</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">Título</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 hidden md:table-cell">Tipo</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 hidden md:table-cell">Estado</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 hidden lg:table-cell">Modificado</th>
                <th className="w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filtered.map((wi) => {
                const typeColor = WORK_ITEM_TYPE_COLOR[wi.work_item_type] ?? "text-gray-400 bg-gray-800";
                return (
                  <tr key={wi.azure_id} className="hover:bg-gray-800/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{wi.azure_id}</td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-gray-200 leading-snug line-clamp-2">{wi.title}</p>
                      {wi.tags && (
                        <p className="text-xs text-gray-600 mt-0.5">{wi.tags}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <span className={cn("text-[10px] px-1.5 py-0.5 rounded font-medium", typeColor)}>
                        {wi.work_item_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <span className="text-xs text-gray-400">{wi.state}</span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      <span className="text-xs text-gray-500">
                        {formatDate(wi.changed_date ?? wi.closed_date)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {wi.url && (
                        <a href={wi.url} target="_blank" rel="noopener" className="btn-ghost py-1 px-1.5">
                          <ExternalLink size={13} />
                        </a>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
