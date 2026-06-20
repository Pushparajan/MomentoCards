"""Seed data for the DocumentType catalog. Encodes the deliverable taxonomy
(flyers, brochures, calendars, cards, ...) as rows so new formats are added by
appending a tuple here rather than branching application code.

Fields: key, name, category, layout_kind, default_page_count, requires_grid, fulfillment_options
"""
from app.models.models import FulfillmentType as FT
from app.models.models import LayoutKind as LK

DIGITAL = FT.digital_export.value
PRINT = f"{FT.digital_export.value},{FT.print_fulfillment.value}"
LIVE = f"{FT.digital_export.value},{FT.live_publish.value}"

CATALOG: list[tuple[str, str, str, LK, int, bool, str]] = [
    # Marketing & Promotional Materials
    ("flyer", "Flyer", "Marketing & Promotional Materials", LK.single_sheet, 1, False, PRINT),
    ("poster", "Poster", "Marketing & Promotional Materials", LK.single_sheet, 1, False, PRINT),
    ("bifold_brochure", "Bi-Fold Brochure", "Marketing & Promotional Materials", LK.folded, 1, False, PRINT),
    ("trifold_brochure", "Tri-Fold Brochure", "Marketing & Promotional Materials", LK.folded, 1, False, PRINT),
    ("leaflet", "Leaflet", "Marketing & Promotional Materials", LK.folded, 1, False, PRINT),
    ("catalog", "Catalog", "Marketing & Promotional Materials", LK.multi_page, 12, False, PRINT),
    ("lookbook", "Lookbook", "Marketing & Promotional Materials", LK.multi_page, 12, False, PRINT),
    ("menu", "Menu", "Marketing & Promotional Materials", LK.single_sheet, 1, False, PRINT),
    ("price_list", "Price List", "Marketing & Promotional Materials", LK.single_sheet, 1, False, DIGITAL),
    ("greeting_card", "Greeting Card", "Marketing & Promotional Materials", LK.folded, 1, False, PRINT),
    ("invitation", "Invitation", "Marketing & Promotional Materials", LK.folded, 1, False, PRINT),
    # Corporate & Business Documents
    ("annual_report", "Annual Report", "Corporate & Business Documents", LK.multi_page, 20, False, DIGITAL),
    ("whitepaper", "Whitepaper", "Corporate & Business Documents", LK.multi_page, 10, False, DIGITAL),
    ("newsletter", "Newsletter", "Corporate & Business Documents", LK.multi_page, 4, False, DIGITAL),
    ("business_card", "Business Card", "Corporate & Business Documents", LK.micro, 1, False, PRINT),
    ("letterhead", "Letterhead", "Corporate & Business Documents", LK.single_sheet, 1, False, PRINT),
    ("manual", "Manual / Instructional Material", "Corporate & Business Documents", LK.multi_page, 30, False, DIGITAL),
    ("presentation", "Presentation", "Corporate & Business Documents", LK.multi_page, 15, False, LIVE),
    ("infographic", "Infographic", "Corporate & Business Documents", LK.single_sheet, 1, False, DIGITAL),
    # Media & Publishing
    ("magazine", "Magazine", "Media & Publishing", LK.multi_page, 24, False, DIGITAL),
    ("newspaper", "Newspaper", "Media & Publishing", LK.multi_page, 8, False, DIGITAL),
    ("book", "Book / eBook", "Media & Publishing", LK.multi_page, 100, False, DIGITAL),
    ("journal", "Journal / Academic Paper", "Media & Publishing", LK.multi_page, 15, False, DIGITAL),
    # Digital Deliverables
    ("digital_magazine", "Digital Magazine / Interactive PDF", "Digital Deliverables", LK.multi_page, 24, False, LIVE),
    ("social_graphic", "Social Media Graphic", "Digital Deliverables", LK.single_sheet, 1, False, LIVE),
    ("web_banner", "Web Banner", "Digital Deliverables", LK.single_sheet, 1, False, LIVE),
    # Calendar Deliverables
    ("wall_calendar", "Wall Calendar", "Calendar Deliverables", LK.grid, 12, True, PRINT),
    ("desk_calendar", "Desk Calendar", "Calendar Deliverables", LK.grid, 12, True, PRINT),
    ("pocket_calendar", "Pocket Calendar", "Calendar Deliverables", LK.grid, 1, True, PRINT),
    ("planner_page", "Planner Page", "Calendar Deliverables", LK.grid, 1, True, PRINT),
    ("magnetic_calendar", "Magnetic Calendar", "Calendar Deliverables", LK.grid, 1, True, PRINT),
    # Card Deliverables
    ("holiday_card", "Greeting & Holiday Card", "Card Deliverables", LK.folded, 1, False, PRINT),
    ("postcard", "Postcard", "Card Deliverables", LK.single_sheet, 1, False, PRINT),
    ("rsvp_card", "Thank You / RSVP Card", "Card Deliverables", LK.micro, 1, False, PRINT),
    ("trading_card", "Trading / Flash Card", "Card Deliverables", LK.micro, 1, False, PRINT),
    # Related Stationery & Novelty Items
    ("certificate", "Certificate / Award", "Related Stationery & Novelty Items", LK.single_sheet, 1, False, DIGITAL),
    ("gift_tag", "Gift Tag / Label", "Related Stationery & Novelty Items", LK.micro, 1, False, PRINT),
    ("bookmark", "Bookmark", "Related Stationery & Novelty Items", LK.micro, 1, False, PRINT),
    ("ticket", "Ticket / Pass", "Related Stationery & Novelty Items", LK.micro, 1, False, PRINT),
    # Digital & Live Publishing
    ("website", "Website / Landing Page", "Digital & Live Publishing", LK.live, 1, False, LIVE),
]
