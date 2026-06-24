"use client";

import { useState } from "react";
import { api, Campaign } from "@/lib/api";

const INTENTS = ["promotion", "event", "announcement"];
const TONES = ["playful", "formal", "urgent", "reassuring"];
const FORMATS = ["Greeting Card", "Invitation", "Social Post", "Print Material"];

export default function IntentStep({ campaign, onAdvance }: { campaign: Campaign; onAdvance: (c: Campaign) => void }) {
  const [format, setFormat] = useState(FORMATS[0]);
  const [goalText, setGoalText] = useState("");
  const [intent, setIntent] = useState(INTENTS[0]);
  const [tones, setTones] = useState<string[]>([]);
  const [audienceHint, setAudienceHint] = useState("");
  const [includeNotes, setIncludeNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleTone(t: string) {
    setTones((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const updated = await api.campaigns.setGoal(campaign.id, {
        goal_text: `[${format}] ${goalText}`,
        intent,
        tones,
        audience_hint: audienceHint || undefined,
        include_notes: includeNotes || undefined,
      });
      onAdvance(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex max-w-xl flex-col gap-4">
      <h2 className="text-lg font-medium">What are you making?</h2>
      <div className="grid grid-cols-2 gap-2">
        {FORMATS.map((f) => (
          <button
            key={f}
            onClick={() => setFormat(f)}
            className={`rounded border px-3 py-2 text-sm ${format === f ? "border-zinc-950 dark:border-zinc-50" : "border-zinc-300 dark:border-zinc-700"}`}
          >
            {f}
          </button>
        ))}
      </div>

      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">What&apos;s the goal or occasion?</span>
        <textarea className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black" value={goalText} onChange={(e) => setGoalText(e.target.value)} />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Intent</span>
        <select className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black" value={intent} onChange={(e) => setIntent(e.target.value)}>
          {INTENTS.map((i) => (
            <option key={i} value={i}>{i}</option>
          ))}
        </select>
      </label>

      <div className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Tone</span>
        <div className="flex flex-wrap gap-2">
          {TONES.map((t) => (
            <button
              key={t}
              onClick={() => toggleTone(t)}
              className={`rounded-full px-3 py-1 text-sm ${tones.includes(t) ? "bg-zinc-950 text-white dark:bg-zinc-50 dark:text-black" : "bg-zinc-100 dark:bg-zinc-800"}`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Who&apos;s it for? (optional)</span>
        <input className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black" value={audienceHint} onChange={(e) => setAudienceHint(e.target.value)} />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-sm text-zinc-500">Anything to include? (optional)</span>
        <input className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black" value={includeNotes} onChange={(e) => setIncludeNotes(e.target.value)} />
      </label>

      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        onClick={submit}
        disabled={submitting || !goalText}
        className="self-end rounded bg-zinc-950 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-50 dark:text-black"
      >
        {submitting ? "Saving…" : "Continue"}
      </button>
    </div>
  );
}
