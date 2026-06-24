"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { api, Campaign, Deliverable } from "@/lib/api";

const CanvasEditor = dynamic(() => import("@/app/components/CanvasEditor"), { ssr: false });

export default function ReviewStep({ campaign, onAdvance }: { campaign: Campaign; onAdvance: (c: Campaign) => void }) {
  const [deliverable, setDeliverable] = useState<Deliverable | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const latestJson = useRef<Record<string, unknown>>({});

  useEffect(() => {
    if (!campaign.deliverable_id) return;
    let cancelled = false;
    const poll = () => {
      api.deliverables.get(campaign.deliverable_id!).then((d) => {
        if (!cancelled) setDeliverable(d);
      });
    };
    poll();
    const interval = setInterval(poll, 2000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [campaign.deliverable_id]);

  async function approve() {
    setSubmitting(true);
    setError(null);
    try {
      await api.campaigns.saveFinalCanvas(campaign.id, latestJson.current);
      const updated = await api.campaigns.review(campaign.id, true);
      onAdvance(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  async function reject() {
    setSubmitting(true);
    setError(null);
    try {
      const updated = await api.campaigns.review(campaign.id, false, "Needs another pass");
      onAdvance(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (!deliverable || deliverable.status === "pending" || deliverable.status === "running") {
    return <p>Still generating — this updates automatically…</p>;
  }
  if (deliverable.status === "failed") {
    return <p className="text-red-600">Generation failed: {deliverable.error}</p>;
  }

  const outputUrl = deliverable.pages[0]?.output_url ?? null;

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-medium">Review your final composition</h2>
      <CanvasEditor
        backgroundImageUrl={outputUrl}
        onChange={(json) => {
          latestJson.current = json;
        }}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2 self-end">
        <button onClick={reject} disabled={submitting} className="rounded border border-zinc-300 px-4 py-2 text-sm disabled:opacity-50 dark:border-zinc-700">
          Request changes
        </button>
        <button onClick={approve} disabled={submitting} className="rounded bg-zinc-950 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-50 dark:text-black">
          {submitting ? "Saving…" : "Approve"}
        </button>
      </div>
    </div>
  );
}
