import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getBitacoras, getConfig } from "../lib/api";
import { formatDate, STATUS_CONFIG } from "../lib/utils";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Spinner } from "../components/ui/Spinner";
import { CalendarDays, CheckCircle2, Clock, AlertCircle, ArrowRight, TrendingUp } from "lucide-react";
import { format, parseISO, isPast } from "date-fns";
import { es } from "date-fns/locale";

export default function Dashboard() {
  const { data: bitacoras, isLoading: loadingBitacoras } = useQuery({
    queryKey: ["bitacoras"],
    queryFn: getBitacoras,
  });

  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: getConfig,
  });

  if (loadingBitacoras) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner className="w-8 h-8" />
      </div>
    );
  }

  const total = bitacoras?.length ?? 0;
  const done = bitacoras?.filter((b) => ["exported", "uploaded"].includes(b.status)).length ?? 0;
  const draft = bitacoras?.filter((b) => b.status === "draft" || b.status === "ready").length ?? 0;
  const overdue = bitacoras?.filter(
    (b) => b.status === "pending" && isPast(parseISO(b.period_end))
  ).length ?? 0;
  const progress = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">
          Seguimiento de tu etapa productiva SENA · {format(new Date(), "EEEE d 'de' MMMM, yyyy", { locale: es })}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={<TrendingUp size={20} />} label="Progreso" value={`${progress}%`} sub={`${done} de ${total} completas`} color="blue" />
        <StatCard icon={<CheckCircle2 size={20} />} label="Completadas" value={done} sub="Exportadas o en OneDrive" color="green" />
        <StatCard icon={<Clock size={20} />} label="En progreso" value={draft} sub="Borradores y listas" color="yellow" />
        <StatCard icon={<AlertCircle size={20} />} label="Atrasadas" value={overdue} sub="Período vencido" color={overdue > 0 ? "red" : "gray"} />
      </div>

      {/* Progress bar */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-300">Progreso total</span>
          <span className="text-sm text-gray-500">{done}/{total} bitácoras</span>
        </div>
        <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 rounded-full transition-all duration-700"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex gap-4 mt-3">
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => {
            const count = bitacoras?.filter((b) => b.status === key).length ?? 0;
            return count > 0 ? (
              <span key={key} className={`text-xs ${cfg.color} flex items-center gap-1`}>
                <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                {count} {cfg.label.toLowerCase()}
              </span>
            ) : null;
          })}
        </div>
      </div>

      {/* Bitácoras grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-100">Todas las bitácoras</h2>
          <Link to="/bitacoras" className="btn-ghost text-xs">
            Ver todas <ArrowRight size={14} />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {bitacoras?.map((b) => {
            const isOverdue = b.status === "pending" && isPast(parseISO(b.period_end));
            const isCurrent = config?.current_bitacora === b.number;

            return (
              <Link
                key={b.id}
                to={`/bitacoras/${b.id}`}
                className="card p-4 hover:border-gray-700 hover:bg-gray-800/50 transition-all group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-gray-500">#{b.number}</span>
                      {isCurrent && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-blue-900/40 text-blue-400 font-medium">
                          Actual
                        </span>
                      )}
                      {isOverdue && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-red-900/40 text-red-400 font-medium">
                          Atrasada
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-gray-200 mt-1 group-hover:text-white transition-colors">
                      Bitácora {b.number}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
                      <CalendarDays size={11} />
                      {formatDate(b.period_start)} → {formatDate(b.period_end)}
                    </p>
                  </div>
                  <StatusBadge status={b.status} size="sm" />
                </div>

                <div className="mt-3 pt-3 border-t border-gray-800 flex items-center justify-between">
                  <span className="text-xs text-gray-600">
                    {b.activity_count > 0 ? `${b.activity_count} actividades` : "Sin actividades"}
                  </span>
                  {b.delivery_date && (
                    <span className="text-xs text-gray-600">
                      Entrega: {formatDate(b.delivery_date)}
                    </span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon, label, value, sub, color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  sub: string;
  color: "blue" | "green" | "yellow" | "red" | "gray";
}) {
  const colors = {
    blue:   "text-blue-400 bg-blue-900/20",
    green:  "text-green-400 bg-green-900/20",
    yellow: "text-yellow-400 bg-yellow-900/20",
    red:    "text-red-400 bg-red-900/20",
    gray:   "text-gray-400 bg-gray-800",
  };

  return (
    <div className="card p-4">
      <div className={`inline-flex p-2 rounded-lg ${colors[color]} mb-3`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-100">{value}</p>
      <p className="text-xs font-medium text-gray-300 mt-0.5">{label}</p>
      <p className="text-xs text-gray-600 mt-0.5">{sub}</p>
    </div>
  );
}
