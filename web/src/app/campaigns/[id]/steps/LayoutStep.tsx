"use client";

import { useEffect, useState } from "react";
import { api, Campaign, DocumentType, LoraTraining } from "@/lib/api";

export default function LayoutStep({ campaign, onAdvance }: { campaign: Campaign; onAdvance: (c: Campaign) => void }) {
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [loras, setLoras] = useState<LoraTraining[]>([]);
  const [documentTypeKey, setDocumentTypeKey] = useState<string | null>(null);
  const [loraId, setLoraId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backgroundUrl, setBackgroundUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api.documentTypes.list().then((types) => {
      setDocumentTypes(types);
      setDocumentTypeKey((prev) => prev ?? types[0]?.key ?? null);
    });
    api.lora.list(campaign.brand_id).then(setLoras);
  }, [campaign.brand_id]);

  async function uploadBackground(file: File) {
    setUploading(true);
    setError(null);
    try {
      const { url } = await api.campaigns.uploadLayoutBackground(campaign.id, file);
      setBackgroundUrl(url);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  }

  async function submit() {
    if (!documentTypeKey) return;
    setSubmitting(true);
    setError(null);
    try {
      const documentType = documentTypes.find((d) => d.key === documentTypeKey);
      const updated = await api.campaigns.setLayout(campaign.id, {
        document_type_key: documentTypeKey,
        style_lora_model_id: loraId,
        canvas_width: 1024,
        canvas_height: 1024,
        grid_pages: documentType?.requires_grid ? [{ month: new Date().getMonth() + 1, year: new Date().getFullYear() }] : null,
      });
      onAdvance(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex max-w-2xl flex-col gap-4">
      <h2 className="text-lg font-medium">Choose a layout</h2>
      <div className="grid grid-cols-3 gap-3">
        {documentTypes.map((dt) => (
          <button
            key={dt.key}
            onClick={() => setDocumentTypeKey(dt.key)}
            className={`rounded border p-3 text-left text-sm ${documentTypeKey === dt.key ? "border-zinc-950 dark:border-zinc-50" : "border-zinc-300 dark:border-zinc-700"}`}
          >
            <div className="font-medium">{dt.name}</div>
            <div className="text-xs text-zinc-500">{dt.category}</div>
          </button>
        ))}
      </div>

      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Brand model (your trained LoRA)</span>
        <select
          className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black"
          value={loraId ?? ""}
          onChange={(e) => setLoraId(e.target.value || null)}
        >
          <option value="">No brand model</option>
          {loras
            .filter((l) => l.is_ready)
            .map((l) => (
              <option key={l.id} value={l.id}>{l.name ?? l.id}</option>
            ))}
        </select>
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Or upload your own image to start from (optional)</span>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => e.target.files?.[0] && uploadBackground(e.target.files[0])}
        />
        {uploading && <span className="text-xs text-zinc-500">Uploading…</span>}
        {backgroundUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={backgroundUrl} alt="Uploaded background" className="mt-1 h-24 w-24 rounded object-cover" />
        )}
      </label>

      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        onClick={submit}
        disabled={submitting || !documentTypeKey}
        className="self-end rounded bg-zinc-950 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-50 dark:text-black"
      >
        {submitting ? "Saving…" : "Continue"}
      </button>
    </div>
  );
}
