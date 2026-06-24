"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { useBrand } from "@/lib/useBrand";

export default function NewCampaignPage() {
  const { brandId } = useBrand();
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function create() {
    if (!brandId) return;
    setCreating(true);
    setError(null);
    try {
      const campaign = await api.campaigns.create(brandId);
      router.push(`/campaigns/${campaign.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCreating(false);
    }
  }

  if (!brandId) {
    return <main className="p-8">Select a brand first.</main>;
  }

  return (
    <main className="p-8 flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Create something new</h1>
      {error && <p className="text-red-600">{error}</p>}
      <button onClick={create} disabled={creating} className="self-start rounded bg-zinc-950 px-4 py-2 text-sm text-white dark:bg-zinc-50 dark:text-black">
        {creating ? "Creating…" : "Start"}
      </button>
    </main>
  );
}
