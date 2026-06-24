"use client";

import { useEffect, useRef, useState } from "react";
import { api, Campaign, GenerateProgressStep } from "@/lib/api";

export default function GenerateStep({ campaign, onAdvance }: { campaign: Campaign; onAdvance: (c: Campaign) => void }) {
  const [steps, setSteps] = useState<GenerateProgressStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    api.campaigns
      .generate(campaign.id)
      .then(onAdvance)
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      api.campaigns.generateProgress(campaign.id).then(setSteps).catch(() => {});
    }, 2000);
    return () => clearInterval(interval);
  }, [campaign.id]);

  return (
    <div className="flex max-w-md flex-col gap-3">
      <h2 className="text-lg font-medium">Generating…</h2>
      <ul className="flex flex-col gap-2">
        {steps.map((s) => (
          <li key={s.label} className="flex items-center justify-between rounded border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-800">
            <span>{s.label}</span>
            <span className="text-xs text-zinc-500">{s.status}</span>
          </li>
        ))}
      </ul>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
