from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage
from app.services.workflow.stages import advance_to, require_stage


def set_goal(db: Session, campaign: Campaign, goal_text: str, intent: str) -> Campaign:
    """Captures the free-text objective ('promote summer sale') and a coarse
    intent tag ('promotion', 'event', 'announcement', ...) that later stages
    (Audience Q&A, prompt building) key off of."""
    require_stage(campaign, CampaignStage.goal)
    campaign.goal = {"goal_text": goal_text, "intent": intent}
    advance_to(campaign, CampaignStage.layout)
    db.commit()
    db.refresh(campaign)
    return campaign
