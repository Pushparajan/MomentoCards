"use client";

import { useState } from "react";
import { api, Campaign } from "@/lib/api";

export default function ContentStep({ campaign, onAdvance }: { campaign: Campaign; onAdvance: (c: Campaign) => void }) {
  const [headline, setHeadline] = useState("");
  const [subheadline, setSubheadline] = useState("");
  const [message, setMessage] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      await api.campaigns.setContentText(campaign.id, { headline, subheadline, message });
      if (photo) await api.campaigns.uploadContentPhotos(campaign.id, [photo]);
      const updated = await api.campaigns.completeContent(campaign.id);
      onAdvance(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex max-w-xl flex-col gap-4">
      <h2 className="text-lg font-medium">Add your content</h2>
      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Headline</span>
        <input className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black" value={headline} onChange={(e) => setHeadline(e.target.value)} />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Subheadline</span>
        <input className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black" value={subheadline} onChange={(e) => setSubheadline(e.target.value)} />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Message</span>
        <textarea className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black" value={message} onChange={(e) => setMessage(e.target.value)} />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Photo (optional)</span>
        <input type="file" accept="image/*" onChange={(e) => setPhoto(e.target.files?.[0] ?? null)} />
      </label>

      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        onClick={submit}
        disabled={submitting}
        className="self-end rounded bg-zinc-950 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-50 dark:text-black"
      >
        {submitting ? "Saving…" : "Continue"}
      </button>
    </div>
  );
}
