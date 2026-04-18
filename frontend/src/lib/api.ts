import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  timeout: 60000,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || "Error desconocido";
    return Promise.reject(new Error(msg));
  }
);

// ─── Types ────────────────────────────────────────────────────────────────────

export type BitacoraStatus = "pending" | "draft" | "ready" | "exported" | "uploaded";

export interface BitacoraListItem {
  id: number;
  number: number;
  period_start: string;
  period_end: string;
  status: BitacoraStatus;
  delivery_date: string | null;
  onedrive_url: string | null;
  activity_count: number;
}

export interface Evidence {
  id: number;
  activity_id: number;
  file_name: string;
  file_type: string;
  file_size: number | null;
  onedrive_url: string | null;
  uploaded_at: string;
}

export interface Activity {
  id: number;
  bitacora_id: number;
  order_index: number;
  title: string;
  description: string;
  competencias: string | null;
  start_date: string | null;
  end_date: string | null;
  evidence_description: string | null;
  observations: string | null;
  azure_work_item_ids: number[] | null;
  is_ai_generated: boolean;
  created_at: string;
  updated_at: string;
  evidence_files: Evidence[];
}

export interface Bitacora extends BitacoraListItem {
  notes: string | null;
  excel_file_path: string | null;
  created_at: string;
  updated_at: string;
  activities: Activity[];
}

export interface WorkItem {
  azure_id: number;
  title: string;
  description: string | null;
  work_item_type: string;
  state: string;
  assigned_to: string | null;
  area_path: string | null;
  tags: string | null;
  completed_work: number | null;
  original_estimate: number | null;
  created_date: string | null;
  changed_date: string | null;
  closed_date: string | null;
  url: string | null;
}

export interface AppConfig {
  total_bitacoras: number;
  current_bitacora: number;
  start_date: string;
  onedrive_configured: boolean;
  periods: Array<{
    number: number;
    start: string;
    end: string;
    label: string;
    delivery_date: string;
  }>;
}

// ─── API calls ────────────────────────────────────────────────────────────────

export const getConfig = () => api.get<AppConfig>("/config").then((r) => r.data);

export const getBitacoras = () =>
  api.get<BitacoraListItem[]>("/bitacoras").then((r) => r.data);

export const getBitacora = (id: number) =>
  api.get<Bitacora>(`/bitacoras/${id}`).then((r) => r.data);

export const updateBitacora = (id: number, data: Partial<Bitacora>) =>
  api.patch<Bitacora>(`/bitacoras/${id}`, data).then((r) => r.data);

export const generateBitacora = (
  id: number,
  workItemIds?: number[],
  regenerate = false,
  aiProvider?: string,
) =>
  api
    .post<Bitacora>(`/bitacoras/${id}/generate`, {
      work_item_ids: workItemIds ?? null,
      regenerate,
      ai_provider: aiProvider ?? null,
    })
    .then((r) => r.data);

export const exportBitacora = (id: number) =>
  api.post<{ download_url: string }>(`/bitacoras/${id}/export`).then((r) => r.data);

export const uploadToOneDrive = (id: number) =>
  api.post<{ url: string }>(`/bitacoras/${id}/upload-onedrive`).then((r) => r.data);

export const updateActivity = (id: number, data: Partial<Activity>) =>
  api.patch<Activity>(`/activities/${id}`, data).then((r) => r.data);

export const deleteActivity = (id: number) =>
  api.delete(`/activities/${id}`).then((r) => r.data);

export const reorderActivities = (ids: number[]) =>
  api.post("/activities/reorder", { activity_ids: ids }).then((r) => r.data);

export const getWorkItemsForBitacora = (bitacoraId: number) =>
  api.get<WorkItem[]>(`/work-items/by-bitacora/${bitacoraId}`).then((r) => r.data);

export const getWorkItems = (startDate: string, endDate: string) =>
  api
    .get<WorkItem[]>("/work-items", { params: { start_date: startDate, end_date: endDate } })
    .then((r) => r.data);

export const syncWorkItems = (startDate: string, endDate: string) =>
  api
    .post<{ count: number }>("/work-items/sync", null, {
      params: { start_date: startDate, end_date: endDate },
    })
    .then((r) => r.data);

export const uploadEvidence = (activityId: number, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api.post<Evidence>(`/evidence/activities/${activityId}`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

export const deleteEvidence = (id: number) =>
  api.delete(`/evidence/${id}`).then((r) => r.data);

export const getEvidenceUrl = (id: number) => `${api.defaults.baseURL}/evidence/file/${id}`;
