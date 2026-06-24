"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Campaign } from "@/lib/api";

export default function LaunchStep({ campaign }: { campaign: Campaign; onAdvance: (c: Campaign) => void }) {
  const [launched, setLaunched] = useState(campaign.stage === "done" ? campaign : null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (launched) return;
    api.campaigns
      .launch(campaign.id)
      .then(setLaunched)
      .catch((e) => setError(e.message));
  }, [campaign.id, launched]);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!launched) return <p>Launching…</p>;

  const outputUrls = (launched.launch.output_urls as string[]) ?? [];

  return (
    <div className="flex flex-col items-start gap-4">
      <h2 className="text-2xl font-semibold">🚀 You launched it!</h2>
      {outputUrls[0] && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={outputUrls[0]} alt="Final result" className="max-w-md rounded border border-zinc-200 dark:border-zinc-800" />
      )}
      <div className="flex gap-2">
        {outputUrls[0] && (
          <a href={outputUrls[0]} download className="rounded border border-zinc-300 px-4 py-2 text-sm dark:border-zinc-700">
            Download image
          </a>
        )}
        <Link href="/library" className="rounded border border-zinc-300 px-4 py-2 text-sm dark:border-zinc-700">
          View in library
        </Link>
        <Link href="/campaigns/new" className="rounded bg-zinc-950 px-4 py-2 text-sm text-white dark:bg-zinc-50 dark:text-black">
          Create another
        </Link>
      </div>
    </div>
  );
}
