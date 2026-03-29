import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";
import type { BitacoraStatus } from "./api";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return format(parseISO(dateStr), "dd/MM/yyyy", { locale: es });
  } catch {
    return dateStr;
  }
}

export function formatDateLong(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return format(parseISO(dateStr), "d 'de' MMMM 'de' yyyy", { locale: es });
  } catch {
    return dateStr;
  }
}

export const STATUS_CONFIG: Record<
  BitacoraStatus,
  { label: string; color: string; bg: string; dot: string }
> = {
  pending:  { label: "Pendiente",  color: "text-gray-400",  bg: "bg-gray-800",       dot: "bg-gray-500"  },
  draft:    { label: "Borrador",   color: "text-yellow-400", bg: "bg-yellow-900/30", dot: "bg-yellow-400" },
  ready:    { label: "Lista",      color: "text-green-400",  bg: "bg-green-900/30",  dot: "bg-green-400" },
  exported: { label: "Exportada",  color: "text-blue-400",   bg: "bg-blue-900/30",   dot: "bg-blue-400"  },
  uploaded: { label: "En OneDrive", color: "text-purple-400", bg: "bg-purple-900/30", dot: "bg-purple-400" },
};

export const WORK_ITEM_TYPE_COLOR: Record<string, string> = {
  Task:       "text-yellow-400 bg-yellow-900/20",
  "User Story": "text-blue-400 bg-blue-900/20",
  Bug:        "text-red-400 bg-red-900/20",
  Feature:    "text-purple-400 bg-purple-900/20",
};
