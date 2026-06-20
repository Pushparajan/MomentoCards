from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Campaign, CampaignStage
from app.services.workflow.stages import advance_to, require_stage

# Base questions asked for every campaign, plus extra ones unlocked by intent.
# Each question is skipped if its `key` is already present in audience answers.
BASE_QUESTIONS = [
    {"key": "target_demographic", "question": "Who is the primary audience for this piece (age range, interests, role)?"},
    {"key": "tone", "question": "What tone should it strike: playful, formal, urgent, or reassuring?"},
]

INTENT_QUESTIONS = {
    "promotion": [
        {"key": "offer_details", "question": "What's the specific offer or discount being promoted?"},
        {"key": "urgency_window", "question": "Is there a deadline or limited-time window to emphasize?"},
    ],
    "event": [
        {"key": "event_datetime", "question": "What is the event date, time, and location?"},
        {"key": "rsvp_action", "question": "What action should attendees take (RSVP link, ticket purchase, walk-in)?"},
    ],
    "announcement": [
        {"key": "key_change", "question": "What is the single most important fact being announced?"},
    ],
}


def _question_bank(campaign: Campaign) -> list[dict]:
    intent = campaign.goal.get("intent", "")
    return BASE_QUESTIONS + INTENT_QUESTIONS.get(intent, [])


def next_question(campaign: Campaign) -> dict | None:
    answers = campaign.audience.get("answers", {})
    for q in _question_bank(campaign):
        if q["key"] not in answers:
            return q
    return None


def answer_question(db: Session, campaign: Campaign, key: str, answer: str) -> Campaign:
    require_stage(campaign, CampaignStage.audience)
    valid_keys = {q["key"] for q in _question_bank(campaign)}
    if key not in valid_keys:
        raise HTTPException(400, f"'{key}' is not a pending question for this campaign")
    audience = campaign.audience
    answers = audience.get("answers", {})
    answers[key] = answer
    audience["answers"] = answers
    campaign.audience = audience
    db.commit()
    db.refresh(campaign)
    return campaign


def complete_audience(db: Session, campaign: Campaign) -> Campaign:
    """Allows moving on once all adaptive questions are answered, or the user
    explicitly skips the remainder."""
    require_stage(campaign, CampaignStage.audience)
    advance_to(campaign, CampaignStage.generate)
    db.commit()
    db.refresh(campaign)
    return campaign
