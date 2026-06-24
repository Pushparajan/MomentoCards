"use client";

import dynamic from "next/dynamic";
import { useRef, useState } from "react";
import { api, Campaign } from "@/lib/api";

const CanvasEditor = dynamic(() => import("@/app/components/CanvasEditor"), { ssr: false });

export default function PreviewStep({ campaign, onAdvance }: { campaign: Campaign; onAdvance: (c: Campaign) => void }) {
  const latestJson = useRef<Record<string, unknown>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function approve() {
    setSubmitting(true);
    setError(null);
    try {
      await api.campaigns.savePreview(campaign.id, latestJson.current);
      const updated = await api.campaigns.approvePreview(campaign.id);
      onAdvance(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-medium">Preview & edit</h2>
      <CanvasEditor
        initialJson={(campaign.preview.canvas_json as Record<string, unknown>) ?? null}
        backgroundImageUrl={
          campaign.preview.canvas_json ? undefined : (campaign.layout.custom_background_url as string | undefined)
        }
        onChange={(json) => {
          latestJson.current = json;
        }}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        onClick={approve}
        disabled={submitting}
        className="self-end rounded bg-zinc-950 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-50 dark:text-black"
      >
        {submitting ? "Saving…" : "Approve & continue"}
      </button>
    </div>
  );
}
