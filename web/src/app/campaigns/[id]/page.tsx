"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, Campaign } from "@/lib/api";
import IntentStep from "./steps/IntentStep";
import LayoutStep from "./steps/LayoutStep";
import ContentStep from "./steps/ContentStep";
import PreviewStep from "./steps/PreviewStep";
import AudienceStep from "./steps/AudienceStep";
import GenerateStep from "./steps/GenerateStep";
import ReviewStep from "./steps/ReviewStep";
import LaunchStep from "./steps/LaunchStep";

const STAGE_LABELS: Record<string, string> = {
  goal: "Intent",
  layout: "Layout",
  content: "Content",
  preview: "Preview",
  audience: "Audience",
  generate: "Generate",
  review: "Review",
  launch: "Launch",
  done: "Done",
};

const STAGE_ORDER = ["goal", "layout", "content", "preview", "audience", "generate", "review", "launch", "done"];

export default function CampaignWizardPage() {
  const params = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.campaigns
      .get(params.id)
      .then(setCampaign)
      .catch((e) => setError(e.message));
  }, [params.id]);

  if (error) return <main className="p-8 text-red-600">{error}</main>;
  if (!campaign) return <main className="p-8">Loading…</main>;

  const currentIdx = STAGE_ORDER.indexOf(campaign.stage);

  return (
    <main className="p-8 flex flex-col gap-8">
      <ol className="flex flex-wrap gap-2 text-xs">
        {STAGE_ORDER.map((stage, i) => (
          <li
            key={stage}
            className={`rounded-full px-3 py-1 ${
              i === currentIdx
                ? "bg-zinc-950 text-white dark:bg-zinc-50 dark:text-black"
                : i < currentIdx
                ? "bg-zinc-200 text-zinc-600 dark:bg-zinc-800"
                : "bg-zinc-100 text-zinc-400 dark:bg-zinc-900"
            }`}
          >
            {STAGE_LABELS[stage]}
          </li>
        ))}
      </ol>

      {campaign.stage === "goal" && <IntentStep campaign={campaign} onAdvance={setCampaign} />}
      {campaign.stage === "layout" && <LayoutStep campaign={campaign} onAdvance={setCampaign} />}
      {campaign.stage === "content" && <ContentStep campaign={campaign} onAdvance={setCampaign} />}
      {campaign.stage === "preview" && <PreviewStep campaign={campaign} onAdvance={setCampaign} />}
      {campaign.stage === "audience" && <AudienceStep campaign={campaign} onAdvance={setCampaign} />}
      {campaign.stage === "generate" && <GenerateStep campaign={campaign} onAdvance={setCampaign} />}
      {campaign.stage === "review" && <ReviewStep campaign={campaign} onAdvance={setCampaign} />}
      {(campaign.stage === "launch" || campaign.stage === "done") && <LaunchStep campaign={campaign} onAdvance={setCampaign} />}
    </main>
  );
}
