"use client";

import { useEffect, useState } from "react";
import { api, Deliverable } from "@/lib/api";
import { useBrand } from "@/lib/useBrand";

type Filter = "all" | "favorites";

export default function LibraryPage() {
  const { brandId } = useBrand();
  const [filter, setFilter] = useState<Filter>("all");
  const [items, setItems] = useState<Deliverable[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!brandId) return;
    api.deliverables
      .list({ brand_id: brandId, favorites_only: filter === "favorites" })
      .then(setItems)
      .catch((e) => setError(e.message));
  }, [brandId, filter]);

  async function toggleFavorite(item: Deliverable) {
    const updated = await api.deliverables.setFavorite(item.id, !item.is_favorite);
    setItems((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
  }

  if (!brandId) {
    return <main className="p-8">Select a brand first.</main>;
  }

  return (
    <main className="p-8 flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Library</h1>
      </div>
      <div className="flex gap-2">
        {(["all", "favorites"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-3 py-1 text-sm ${
              filter === f ? "bg-zinc-950 text-white dark:bg-zinc-50 dark:text-black" : "bg-zinc-100 dark:bg-zinc-800"
            }`}
          >
            {f === "all" ? "All" : "Favorites"}
          </button>
        ))}
      </div>
      {error && <p className="text-red-600">{error}</p>}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {items.map((item) => (
          <div key={item.id} className="rounded border border-zinc-200 p-3 dark:border-zinc-800">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{item.title ?? "Untitled"}</span>
              <button onClick={() => toggleFavorite(item)} aria-label="favorite">
                {item.is_favorite ? "♥" : "♡"}
              </button>
            </div>
            <div className="text-xs text-zinc-500">{item.status}</div>
            {item.pages[0]?.output_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={item.pages[0].output_url} alt={item.title ?? ""} className="mt-2 aspect-square w-full rounded object-cover" />
            )}
          </div>
        ))}
        {items.length === 0 && <p className="text-sm text-zinc-500">No creations yet.</p>}
      </div>
    </main>
  );
}
