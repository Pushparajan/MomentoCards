"use client";

import { useEffect, useState } from "react";
import { api, Campaign } from "@/lib/api";

export default function AudienceStep({ campaign, onAdvance }: { campaign: Campaign; onAdvance: (c: Campaign) => void }) {
  const [question, setQuestion] = useState<{ key: string; question: string } | null | undefined>(undefined);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function loadNext() {
    api.campaigns.nextAudienceQuestion(campaign.id).then(setQuestion);
  }

  useEffect(loadNext, [campaign.id]);

  async function submitAnswer() {
    if (!question) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.campaigns.answerAudience(campaign.id, question.key, answer);
      setAnswer("");
      loadNext();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  async function finish() {
    setSubmitting(true);
    setError(null);
    try {
      const updated = await api.campaigns.completeAudience(campaign.id);
      onAdvance(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (question === undefined) return <p>Loading…</p>;

  return (
    <div className="flex max-w-xl flex-col gap-4">
      <h2 className="text-lg font-medium">A few quick questions</h2>
      {question ? (
        <div className="flex flex-col gap-2">
          <p className="text-sm">{question.question}</p>
          <input
            className="rounded border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-black"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
          <button
            onClick={submitAnswer}
            disabled={submitting || !answer}
            className="self-end rounded bg-zinc-950 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-zinc-50 dark:text-black"
          >
            Next
          </button>
        </div>
      ) : (
        <p className="text-sm text-zinc-500">All set — no more questions.</p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        onClick={finish}
        disabled={submitting}
        className="self-end rounded border border-zinc-300 px-4 py-2 text-sm disabled:opacity-50 dark:border-zinc-700"
      >
        {question ? "Skip remaining & continue" : "Continue"}
      </button>
    </div>
  );
}
