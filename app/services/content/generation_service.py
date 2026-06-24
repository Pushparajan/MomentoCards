from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.content_models import (
    BrandProfile,
    ContentStatus,
    ContentTemplate,
    ContentVersion,
    GeneratedContent,
    TemplateStatus,
)
from app.services.audit_log import record as audit_record
from app.services.content.policy_engine import enforce_banned_terms

LENGTH_TARGETS = {"short": 60, "medium": 150, "long": 400}


def _compose(template: ContentTemplate, profile: BrandProfile, prompt_brief: str, keywords: list[str], output_length: str) -> str:
    """Deterministic, provider-agnostic composition: fills the template body
    with brief/keywords/tone so the workflow is fully testable without a live
    LLM call. Swappable later for a real generation provider behind this one
    function."""
    keyword_line = f"Keywords: {', '.join(keywords)}\n" if keywords else ""
    vocabulary_hint = f"Preferred vocabulary: {', '.join(profile.vocabulary_list())}\n" if profile.vocabulary_list() else ""
    body = (
        f"{template.body}\n\n"
        f"Brief: {prompt_brief}\n"
        f"{keyword_line}"
        f"Tone: {profile.tone or 'neutral'}\n"
        f"{vocabulary_hint}"
        f"[Target length: {output_length} (~{LENGTH_TARGETS.get(output_length, 150)} words)]"
    )
    return body


def generate(
    db: Session,
    template: ContentTemplate,
    profile: BrandProfile,
    campaign_name: str | None,
    prompt_brief: str,
    keywords: list[str],
    output_length: str,
) -> GeneratedContent:
    if template.status == TemplateStatus.archived:
        raise HTTPException(400, "Cannot generate from an archived template")
    if profile.status == TemplateStatus.archived:
        raise HTTPException(400, "Cannot generate with an archived brand profile")

    content = GeneratedContent(
        template_id=template.id,
        brand_profile_id=profile.id,
        campaign_name=campaign_name,
        prompt_brief=prompt_brief,
        keywords=",".join(keywords),
        output_length=output_length,
        status=ContentStatus.draft,
    )
    db.add(content)
    db.commit()

    try:
        body = _compose(template, profile, prompt_brief, keywords, output_length)
        enforce_banned_terms(body, profile)
        db.add(ContentVersion(content_id=content.id, version_number=1, body=body, change_type="generate"))
    except HTTPException as exc:
        content.status = ContentStatus.draft
        content.error = exc.detail
        db.commit()
        db.refresh(content)
        audit_record(db, "generate_failed", content_id=content.id, detail={"error": exc.detail})
        raise

    db.commit()
    db.refresh(content)
    audit_record(db, "generate", content_id=content.id, detail={"template_id": template.id, "brand_profile_id": profile.id})
    return content


def rewrite(db: Session, content: GeneratedContent, rewrite_type: str, params: dict) -> GeneratedContent:
    latest = content.latest_version()
    if not latest:
        raise HTTPException(400, "Content has no draft to rewrite yet")

    body = latest.body
    if rewrite_type == "tone" and params.get("tone"):
        body += f"\n[Rewritten tone: {params['tone']}]"
    elif rewrite_type == "length" and params.get("output_length"):
        content.output_length = params["output_length"]
        body += f"\n[Rewritten length: {params['output_length']} (~{LENGTH_TARGETS.get(params['output_length'], 150)} words)]"
    elif rewrite_type == "cta" and params.get("cta_focus"):
        body += f"\n[CTA focus: {params['cta_focus']}]"
    elif rewrite_type == "language" and params.get("language"):
        body += f"\n[Translated to: {params['language']}]"
    else:
        raise HTTPException(400, f"Missing parameter for rewrite_type '{rewrite_type}'")

    profile: BrandProfile = content.brand_profile
    enforce_banned_terms(body, profile)

    next_version_number = latest.version_number + 1
    db.add(ContentVersion(content_id=content.id, version_number=next_version_number, body=body, change_type="rewrite"))
    content.status = ContentStatus.draft
    db.commit()
    db.refresh(content)
    audit_record(db, "rewrite", content_id=content.id, detail={"rewrite_type": rewrite_type})
    return content
