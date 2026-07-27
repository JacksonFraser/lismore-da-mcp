"""Discovering the SEE form's geometry from the PDF itself.

The blank template carries no AcroForm fields, so answers are drawn onto
rectangles located at fill time and addressed by index. SEE_LAYOUT_EXPECTED makes
a reissued form fail loudly rather than silently misplacing an applicant's
details. See tests/test_see_layout.py.
"""

import fitz  # PyMuPDF

# Wingdings empty squares: U+F0A8 on the Yes/No rows, U+F071 on page 1
CHECKBOX_GLYPHS = {"\uf0a8", "\uf071"}

# (boxes, checkboxes) expected per page — guards against template changes
SEE_LAYOUT_EXPECTED = {
    0: (8, 1),
    1: (3, 0),
    2: (3, 8),
    3: (3, 18),
    4: (3, 28),
    5: (3, 20),
    6: (8, 0),
    7: (0, 0),
}

def _answer_boxes(page) -> list:
    """White-filled input boxes on a page, in reading order."""
    boxes, seen = [], set()
    for drawing in page.get_drawings():
        rect = drawing["rect"]
        if drawing.get("fill") != (1.0, 1.0, 1.0):
            continue
        if rect.width < 30 or rect.height < 10:
            continue
        key = (round(rect.x0, 1), round(rect.y0, 1), round(rect.x1, 1), round(rect.y1, 1))
        if key in seen:
            continue
        seen.add(key)
        boxes.append(rect)
    boxes.sort(key=lambda r: (round(r.y0), r.x0))
    return boxes

def _checkbox_rects(page) -> list:
    """Tick box glyph rectangles on a page, in reading order."""
    rects = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                for char in span.get("chars", []):
                    if char["c"] in CHECKBOX_GLYPHS:
                        rects.append(fitz.Rect(char["bbox"]))
    rects.sort(key=lambda r: (round(r.y0), r.x0))
    return rects

def see_layout(doc) -> dict:
    """Map each page to its answer boxes and tick boxes, discovered from the PDF."""
    return {
        page_num: {
            "boxes": _answer_boxes(doc[page_num]),
            "checks": _checkbox_rects(doc[page_num]),
        }
        for page_num in range(len(doc))
    }
