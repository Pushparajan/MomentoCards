from sqlalchemy.orm import Session

from app.models.models import Template


def find_best_template(db: Session, document_type_id: str, category: str | None, goal_text: str) -> Template | None:
    """Template Intelligence layer: retrieves the best-matching Template for
    a campaign's document type + category + free-text goal. Today this is
    keyword/category matching (cheap, deterministic, no extra infra); an
    embedding-based vector search (Template RAG) is a deferred upgrade that
    can replace this function's body without touching its callers."""
    query = db.query(Template).filter(Template.document_type_id == document_type_id)
    if category:
        query = query.filter(Template.category == category)
    candidates = query.all()
    if not candidates:
        return None

    goal_words = {w.lower() for w in goal_text.split()}

    def score(template: Template) -> int:
        return len(goal_words & {t.lower() for t in template.tag_list()})

    return max(candidates, key=score)
