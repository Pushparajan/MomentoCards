const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${path}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface Organization {
  id: string;
  name: string;
  created_at: string;
}

export interface Brand {
  id: string;
  name: string;
  organization_id: string | null;
  primary_color: string | null;
  secondary_color: string | null;
  mood_keywords: string | null;
  created_at: string;
}

export interface LoraTraining {
  id: string;
  brand_id: string;
  category: string;
  status: string;
  is_ready: boolean;
  error: string | null;
}

export interface DocumentType {
  id: string;
  key: string;
  name: string;
  category: string;
  layout_kind: string;
  default_page_count: number;
  requires_grid: boolean;
  fulfillment_options: string[];
}

export interface DeliverablePage {
  id: string;
  page_number: number;
  status: string;
  output_url: string | null;
  error: string | null;
}

export interface Deliverable {
  id: string;
  brand_id: string;
  document_type_id: string;
  title: string | null;
  style: string;
  status: string;
  error: string | null;
  pages: DeliverablePage[];
}

export interface Campaign {
  id: string;
  brand_id: string;
  deliverable_id: string | null;
  stage: string;
  goal: Record<string, unknown>;
  layout: Record<string, unknown>;
  content: Record<string, unknown>;
  preview: Record<string, unknown>;
  audience: Record<string, unknown>;
  review: Record<string, unknown>;
  launch: Record<string, unknown>;
}

export const api = {
  organizations: {
    create: (name: string) => request<Organization>("/organizations", { method: "POST", body: JSON.stringify({ name }) }),
    get: (id: string) => request<Organization>(`/organizations/${id}`),
  },
  brands: {
    create: (payload: { name: string; organization_id?: string; primary_color?: string; secondary_color?: string; mood_keywords?: string }) =>
      request<Brand>("/brands", { method: "POST", body: JSON.stringify(payload) }),
    get: (id: string) => request<Brand>(`/brands/${id}`),
    uploadAssets: (brandId: string, files: File[]) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      return request<{ saved: string[] }>(`/brands/${brandId}/assets`, { method: "POST", body: form });
    },
  },
  lora: {
    uploadAndTrain: (brandId: string, files: File[], category = "branding") => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      return request<LoraTraining>(`/brands/${brandId}/lora/train-from-upload?category=${category}`, {
        method: "POST",
        body: form,
      });
    },
    train: (brandId: string, category = "branding") =>
      request<LoraTraining>(`/brands/${brandId}/train?category=${category}`, { method: "POST" }),
    getStatus: (brandId: string, loraId: string) => request<LoraTraining>(`/brands/${brandId}/train/${loraId}`),
    list: (brandId: string) => request<LoraTraining[]>(`/brands/${brandId}/loras`),
  },
  documentTypes: {
    list: () => request<DocumentType[]>("/document-types"),
  },
  deliverables: {
    create: (payload: {
      brand_id: string;
      document_type_key: string;
      title?: string;
      style?: string;
      use_brand_lora?: boolean;
      ip_adapter_asset_id?: string;
      pages?: { params: Record<string, unknown> }[];
    }) => request<Deliverable>("/deliverables", { method: "POST", body: JSON.stringify(payload) }),
    get: (id: string) => request<Deliverable>(`/deliverables/${id}`),
    generateVideo: (pageId: string, prompt?: string) =>
      request<DeliverablePage>(`/deliverables/pages/${pageId}/video`, {
        method: "POST",
        body: JSON.stringify({ prompt }),
      }),
  },
  campaigns: {
    create: (brandId: string) => request<Campaign>("/campaigns", { method: "POST", body: JSON.stringify({ brand_id: brandId }) }),
    get: (id: string) => request<Campaign>(`/campaigns/${id}`),
    setGoal: (id: string, goalText: string, intent: string) =>
      request<Campaign>(`/campaigns/${id}/goal`, { method: "POST", body: JSON.stringify({ goal_text: goalText, intent }) }),
    setLayout: (id: string, payload: Record<string, unknown>) =>
      request<Campaign>(`/campaigns/${id}/layout`, { method: "POST", body: JSON.stringify(payload) }),
    setContent: (id: string, textFields: Record<string, unknown>) =>
      request<Campaign>(`/campaigns/${id}/content`, { method: "POST", body: JSON.stringify({ text_fields: textFields }) }),
    savePreview: (id: string, canvasJson: Record<string, unknown>) =>
      request<Campaign>(`/campaigns/${id}/preview`, { method: "POST", body: JSON.stringify({ canvas_json: canvasJson }) }),
    answerAudience: (id: string, key: string, answer: string) =>
      request<Campaign>(`/campaigns/${id}/audience`, { method: "POST", body: JSON.stringify({ key, answer }) }),
    generate: (id: string) => request<Campaign>(`/campaigns/${id}/generate`, { method: "POST" }),
    saveFinalCanvas: (id: string, canvasJson: Record<string, unknown>) =>
      request<Campaign>(`/campaigns/${id}/final-canvas`, { method: "POST", body: JSON.stringify({ canvas_json: canvasJson }) }),
    review: (id: string, approved: boolean, comments?: string) =>
      request<Campaign>(`/campaigns/${id}/review`, { method: "POST", body: JSON.stringify({ approved, comments }) }),
    launch: (id: string) => request<Campaign>(`/campaigns/${id}/launch`, { method: "POST" }),
  },
};
