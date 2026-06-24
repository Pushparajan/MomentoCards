from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage
from app.services.workflow.stages import advance_to, require_stage


def set_goal(
    db: Session,
    campaign: Campaign,
    goal_text: str,
    intent: str,
    tones: list[str] | None = None,
    audience_hint: str | None = None,
    include_notes: str | None = None,
) -> Campaign:
    """Captures the free-text objective ('promote summer sale'), a coarse
    intent tag ('promotion', 'event', 'announcement', ...), and the mock's
    Intent-step extras (tone chips, audience hint, anything-to-include notes)
    that later stages (Audience Q&A, prompt building) key off of."""
    require_stage(campaign, CampaignStage.goal)
    campaign.goal = {
        "goal_text": goal_text,
        "intent": intent,
        "tones": tones or [],
        "audience_hint": audience_hint,
        "include_notes": include_notes,
    }
    advance_to(campaign, CampaignStage.layout)
    db.commit()
    db.refresh(campaign)
    return campaign
