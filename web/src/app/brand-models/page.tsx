"use client";

import { useEffect, useState } from "react";
import { api, LoraTraining } from "@/lib/api";
import { useBrand } from "@/lib/useBrand";

export default function BrandModelsPage() {
  const { brandId } = useBrand();
  const [models, setModels] = useState<LoraTraining[]>([]);
  const [showWizard, setShowWizard] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    if (!brandId) return;
    api.lora.list(brandId).then(setModels).catch((e) => setError(e.message));
  }

  useEffect(refresh, [brandId]);

  async function retry(model: LoraTraining) {
    if (!brandId) return;
    await api.lora.retry(brandId, model.id);
    refresh();
  }

  if (!brandId) {
    return <main className="p-8">Select a brand first.</main>;
  }

  return (
    <main className="p-8 flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Your custom models</h1>
        <button
          onClick={() => setShowWizard(true)}
          className="rounded bg-zinc-950 px-4 py-2 text-sm text-white dark:bg-zinc-50 dark:text-black"
        >
          + Train model
        </button>
      </div>
      {error && <p className="text-red-600">{error}</p>}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {models.map((m) => (
          <div key={m.id} className="rounded border border-zinc-200 p-4 dark:border-zinc-800">
            <div className="text-xs uppercase text-zinc-500">{m.subject_type}</div>
            <div className="font-medium">{m.name ?? "Untitled model"}</div>
            <div className="text-sm text-zinc-500">{m.status}</div>
            {m.status === "failed" && (
              <button onClick={() => retry(m)} className="mt-2 text-sm text-blue-600 underline">
                Retry
              </button>
            )}
          </div>
        ))}
        {models.length === 0 && <p className="text-sm text-zinc-500">No models trained yet.</p>}
      </div>
      {showWizard && (
        <TrainWizard
          brandId={brandId}
          onClose={() => setShowWizard(false)}
          onDone={() => {
            setShowWizard(false);
            refresh();
          }}
        />
      )}
    </main>
  );
}

function TrainWizard({ brandId, onClose, onDone }: { brandId: string; onClose: () => void; onDone: () => void }) {
  const [step, setStep] = useState(1);
  const [subjectType, setSubjectType] = useState<"style" | "subject">("style");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      const qs = new URLSearchParams({ subject_type: subjectType, name, description });
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/brands/${brandId}/lora/train-from-upload?${qs.toString()}`,
        { method: "POST", body: form }
      );
      if (!res.ok) throw new Error(await res.text());
      onDone();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded bg-white p-6 dark:bg-zinc-900">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Train a custom model</h2>
          <button onClick={onClose}>✕</button>
        </div>
        {step === 1 && (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-zinc-500">What are you training?</p>
            {(["style", "subject"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setSubjectType(t)}
                className={`rounded border px-3 py-2 text-left text-sm ${
                  subjectType === t ? "border-zinc-950 dark:border-zinc-50" : "border-zinc-300 dark:border-zinc-700"
                }`}
              >
                {t === "style" ? "Style — a visual look/feel" : "Subject — a consistent character/product"}
              </button>
            ))}
            <button onClick={() => setStep(2)} className="self-end rounded bg-zinc-950 px-4 py-2 text-sm text-white dark:bg-zinc-50 dark:text-black">
              Next
            </button>
          </div>
        )}
        {step === 2 && (
          <div className="flex flex-col gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-sm text-zinc-500">Model name</span>
              <input className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black" value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-sm text-zinc-500">Description (optional)</span>
              <textarea className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black" value={description} onChange={(e) => setDescription(e.target.value)} />
            </label>
            <button onClick={() => setStep(3)} className="self-end rounded bg-zinc-950 px-4 py-2 text-sm text-white dark:bg-zinc-50 dark:text-black">
              Next
            </button>
          </div>
        )}
        {step === 3 && (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-zinc-500">Upload reference images (4–20)</p>
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            />
            <div className="grid grid-cols-4 gap-2">
              {files.map((f, i) => (
                <div key={i} className="aspect-square rounded bg-zinc-100 p-1 text-center text-[10px] dark:bg-zinc-800">
                  {f.name}
                </div>
              ))}
            </div>
            {files.length > 0 && (
              <button onClick={() => setFiles([])} className="self-start text-sm text-zinc-500 underline">
                Clear all
              </button>
            )}
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              onClick={submit}
              disabled={submitting || files.length < 4}
              className="self-end rounded bg-zinc-950 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-50 dark:text-black"
            >
              {submitting ? "Training…" : "Train model"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
