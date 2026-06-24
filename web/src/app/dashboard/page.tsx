"use client";

import { useEffect, useState } from "react";
import { api, DashboardOverview } from "@/lib/api";
import { useBrand } from "@/lib/useBrand";

export default function DashboardPage() {
  const { brandId } = useBrand();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!brandId) return;
    api.dashboard
      .overview(brandId)
      .then(setOverview)
      .catch((e) => setError(e.message));
  }, [brandId]);

  if (!brandId) {
    return <main className="p-8">Select a brand first (set one up via the Brand Models page or API).</main>;
  }
  if (error) {
    return <main className="p-8 text-red-600">{error}</main>;
  }
  if (!overview) {
    return <main className="p-8">Loading…</main>;
  }

  return (
    <main className="p-8 flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Overview</h1>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Total creations" value={overview.total_creations} />
        <Stat label="Favorites" value={overview.favorites_count} />
        <Stat label="Brand models" value={`${overview.brand_models_ready}/${overview.brand_models_total} ready`} />
        <Stat label="Most made" value={overview.most_made_document_type ?? "—"} />
      </div>
      <section>
        <h2 className="mb-2 text-lg font-medium">Recent work</h2>
        <ul className="flex flex-col gap-2">
          {overview.recent.map((item) => (
            <li key={item.id} className="rounded border border-zinc-200 p-3 text-sm dark:border-zinc-800">
              <span className="font-medium">{item.title ?? "Untitled"}</span> — {item.status}
            </li>
          ))}
          {overview.recent.length === 0 && <li className="text-sm text-zinc-500">Nothing created yet.</li>}
        </ul>
      </section>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="text-sm text-zinc-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}
