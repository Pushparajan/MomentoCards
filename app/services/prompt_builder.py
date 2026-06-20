STRUCTURAL_STYLE_TAGS = (
    "clean grid layout, professional calendar design, flat vector illustration, "
    "minimalist corporate design, crisp typography, sharp legible numbers, "
    "high contrast text, aligned to grid lines"
)

NEGATIVE_DEFAULT = (
    "blurry, distorted text, warped letters, photographic clutter, busy background, "
    "low contrast, illegible numbers, messy grid, overlapping cells"
)


def build_prompt(style: str, mood_keywords: str | None, primary_color: str | None, secondary_color: str | None) -> str:
    """Implements the 'Style-Aligned Prompting Approach': brand colors/mood are
    injected directly into the prompt around the structural/style LoRA tags,
    avoiding a need for a custom LoRA per brand when one hasn't been trained."""
    parts = [STRUCTURAL_STYLE_TAGS, f"style: {style}"]
    if primary_color:
        parts.append(f"primary brand color {primary_color}")
    if secondary_color:
        parts.append(f"secondary brand color {secondary_color}")
    if mood_keywords:
        parts.append(mood_keywords)
    return ", ".join(parts)


def build_negative_prompt() -> str:
    return NEGATIVE_DEFAULT
