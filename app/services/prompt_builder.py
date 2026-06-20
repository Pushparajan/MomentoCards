from app.models.models import LayoutKind

BASE_STYLE_TAGS = (
    "professional graphic design, flat vector illustration, minimalist corporate "
    "design, crisp typography, high contrast text"
)

LAYOUT_TAGS = {
    LayoutKind.single_sheet: "single-sheet layout, clear focal point, bold call-to-action area",
    LayoutKind.folded: "panel-based fold layout, distinct front and inner panels, consistent margins across panels",
    LayoutKind.multi_page: "consistent multi-page layout, repeating header/footer grid, aligned columns",
    LayoutKind.grid: "clean grid layout, square grid segments, sharp legible numbers, aligned to grid lines",
    LayoutKind.micro: "small-format layout, centered composition, legible at small scale",
    LayoutKind.live: "responsive web layout, clear visual hierarchy, platform-safe aspect ratio",
}

NEGATIVE_DEFAULT = (
    "blurry, distorted text, warped letters, photographic clutter, busy background, "
    "low contrast, illegible numbers, messy grid, overlapping cells, inconsistent panels"
)


def build_prompt(
    layout_kind: LayoutKind,
    style: str,
    mood_keywords: str | None,
    primary_color: str | None,
    secondary_color: str | None,
    page_context: str | None = None,
) -> str:
    """Implements the 'Style-Aligned Prompting Approach': brand colors/mood are
    injected directly into the prompt around the structural/style LoRA tags,
    avoiding a need for a custom LoRA per brand when one hasn't been trained.
    `layout_kind` swaps in the structural tags for the deliverable's shape
    (single sheet, folded panels, multi-page, grid, micro, live)."""
    parts = [BASE_STYLE_TAGS, LAYOUT_TAGS[layout_kind], f"style: {style}"]
    if primary_color:
        parts.append(f"primary brand color {primary_color}")
    if secondary_color:
        parts.append(f"secondary brand color {secondary_color}")
    if mood_keywords:
        parts.append(mood_keywords)
    if page_context:
        parts.append(page_context)
    return ", ".join(parts)


def build_negative_prompt() -> str:
    return NEGATIVE_DEFAULT
