"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ProfilePage() {
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.profile.get().then((p) => {
      setEmail(p.email);
      setDisplayName(p.display_name ?? "");
    });
  }, []);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.profile.update(displayName);
      setDisplayName(updated.display_name ?? "");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="p-8 max-w-md flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Account info</h1>
      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Display name</span>
        <input
          className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Email</span>
        <input className="rounded border border-zinc-300 px-3 py-2 text-zinc-500 dark:border-zinc-700" value={email} disabled />
        <span className="text-xs text-zinc-500">Email can&apos;t be changed.</span>
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        onClick={save}
        disabled={saving}
        className="self-start rounded bg-zinc-950 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-50 dark:text-black"
      >
        {saving ? "Saving…" : "Save changes"}
      </button>
      <button className="self-start text-sm text-zinc-500 underline">Sign out</button>
    </main>
  );
}
