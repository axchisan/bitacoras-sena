import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getBitacoras } from "../lib/api";
import { formatDate } from "../lib/utils";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Spinner } from "../components/ui/Spinner";
import { CalendarDays, ArrowRight, BookOpen } from "lucide-react";
import { isPast, parseISO } from "date-fns";

export default function BitacoraList() {
  const { data: bitacoras, isLoading } = useQuery({
    queryKey: ["bitacoras"],
    queryFn: getBitacoras,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner className="w-8 h-8" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Bitácoras</h1>
        <p className="text-gray-500 text-sm mt-1">
          12 bitácoras · 15 días calendario cada una
        </p>
      </div>

      <div className="space-y-2">
        {bitacoras?.map((b) => {
          const isOverdue = b.status === "pending" && isPast(parseISO(b.period_end));

          return (
            <Link
              key={b.id}
              to={`/bitacoras/${b.id}`}
              className="card p-4 flex items-center gap-4 hover:border-gray-700 hover:bg-gray-800/40 transition-all group"
            >
              {/* Number */}
              <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center text-sm font-bold text-gray-400 shrink-0 group-hover:bg-blue-900/30 group-hover:text-blue-400 transition-all">
                {b.number}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-200 group-hover:text-white transition-colors">
                    Bitácora {b.number}
                  </span>
                  {isOverdue && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-red-900/40 text-red-400">
                      Atrasada
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
                  <CalendarDays size={11} />
                  {formatDate(b.period_start)} → {formatDate(b.period_end)}
                  {b.delivery_date && (
                    <span className="ml-2">· Entrega: {formatDate(b.delivery_date)}</span>
                  )}
                </p>
              </div>

              {/* Activities */}
              <div className="hidden sm:flex items-center gap-1 text-xs text-gray-600 shrink-0">
                <BookOpen size={12} />
                {b.activity_count} actividades
              </div>

              {/* Status */}
              <StatusBadge status={b.status} size="sm" />

              {/* Arrow */}
              <ArrowRight size={16} className="text-gray-700 group-hover:text-gray-400 transition-colors shrink-0" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
