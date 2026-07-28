"""Drawing answers onto the SEE PDF.

Text is shrunk to fit its discovered box and reported as overflowed when it
cannot, so the caller knows a continuation attachment is needed rather than
silently losing the text.
"""

from pathlib import Path

import fitz  # PyMuPDF

from lismore_da_mcp.observability import record_document_error

from lismore_da_mcp.config import SEE_TEMPLATE_PATH
from lismore_da_mcp.see.fields import SEE_FORM_FIELDS
from lismore_da_mcp.see.layout import SEE_LAYOUT_EXPECTED, see_layout

FILL_FONT = "helv"

FILL_FONT_OBJ = fitz.Font(FILL_FONT)

BOX_PADDING = 3          # points of clearance inside each answer box

MAX_FONTSIZE = 10.0

MIN_FONTSIZE = 6.5       # below this the form stops being legible when printed

def _draw_tick(page, rect) -> None:
    """Draw a cross inside the tick box, sized to the box."""
    inset = rect.width * 0.22
    box = fitz.Rect(rect.x0 + inset, rect.y0 + inset, rect.x1 - inset, rect.y1 - inset)
    width = max(0.8, rect.width * 0.09)
    page.draw_line(box.tl, box.br, color=(0, 0, 0), width=width)
    page.draw_line(box.bl, box.tr, color=(0, 0, 0), width=width)

def _write(page, area, text: str, fontsize: float) -> list:
    """Write text into area, returning the lines that didn't fit.

    TextWriter is used rather than Page.insert_textbox because it writes the
    part that fits and hands back the remainder, instead of discarding the whole
    field when the text is too long.
    """
    writer = fitz.TextWriter(page.rect)
    leftover = writer.fill_textbox(
        area,
        text,
        font=FILL_FONT_OBJ,
        fontsize=fontsize,
        align=fitz.TEXT_ALIGN_LEFT,
        warn=None,  # None = stay silent on overflow; True warns, False raises
    )
    writer.write_text(page, color=(0, 0, 0))
    return leftover or []

def _draw_single_line(page, rect, text: str) -> bool:
    """Draw one line of text, vertically centred in the box, shrinking to fit its width.

    Returns False when the value is too long even at the minimum size; it is
    then ellipsised rather than printed across the form's labels.
    """
    width = rect.width - 2 * BOX_PADDING
    fontsize = min(MAX_FONTSIZE, rect.height * 0.62)

    while (fitz.get_text_length(text, fontname=FILL_FONT, fontsize=fontsize) > width
           and fontsize > MIN_FONTSIZE):
        fontsize -= 0.25

    fits = fitz.get_text_length(text, fontname=FILL_FONT, fontsize=fontsize) <= width
    if not fits:
        while text and fitz.get_text_length(text + "…", fontname=FILL_FONT, fontsize=fontsize) > width:
            text = text[:-1]
        text = text.rstrip() + "…"

    line_height = fontsize * 1.2
    top = rect.y0 + max(0, (rect.height - line_height) / 2)
    _write(page, fitz.Rect(rect.x0 + BOX_PADDING, top, rect.x1 - BOX_PADDING, rect.y1), text, fontsize)
    return fits

def _draw_wrapped(page, rect, text: str) -> bool:
    """Draw wrapped text inside the box, shrinking to fit.

    Returns False if the text still doesn't fit at the minimum size — as much as
    fits is written, and the caller reports the field so the rest can go on an
    attachment page.
    """
    area = rect + (BOX_PADDING, BOX_PADDING, -BOX_PADDING, -BOX_PADDING)
    fontsize = MAX_FONTSIZE

    while fontsize > MIN_FONTSIZE:
        # Measure on a throwaway copy so a failed attempt leaves no ink behind.
        probe = fitz.open()
        probe_page = probe.new_page(width=page.rect.width, height=page.rect.height)
        if not _write(probe_page, area, text, fontsize):
            probe.close()
            _write(page, area, text, fontsize)
            return True
        probe.close()
        fontsize -= 0.5

    return not _write(page, area, text, MIN_FONTSIZE)

def fill_see_pdf(form_data: dict, output_path: Path) -> dict:
    """Fill the SEE PDF template and save to output_path.

    Returns {"success": bool, ...} with any layout warnings — fields whose text
    was too long for the printed box (those need a continuation attachment) and
    any field whose box couldn't be located in the template.
    """
    try:
        doc = fitz.open(SEE_TEMPLATE_PATH)
        layout = see_layout(doc)

        overflowed: list[str] = []
        unresolved: list[str] = []
        template_changed: list[str] = []

        for page_num, (want_boxes, want_checks) in SEE_LAYOUT_EXPECTED.items():
            found = layout.get(page_num)
            if found is None:
                template_changed.append(f"page {page_num + 1} missing")
                continue
            got = (len(found["boxes"]), len(found["checks"]))
            if got != (want_boxes, want_checks):
                template_changed.append(
                    f"page {page_num + 1}: expected {want_boxes} boxes/{want_checks} tick boxes, found {got[0]}/{got[1]}"
                )

        for field_name, field_config in SEE_FORM_FIELDS.items():
            value = form_data.get(field_name)
            if value is None:
                continue

            page_num = field_config["page"]
            if page_num >= len(doc):
                unresolved.append(field_name)
                continue
            page = doc[page_num]

            if "check" in field_config:
                if not value:
                    continue  # unticked boxes are left as the form prints them
                checks = layout[page_num]["checks"]
                index = field_config["check"]
                if index >= len(checks):
                    unresolved.append(field_name)
                    continue
                _draw_tick(page, checks[index])
                continue

            text = str(value).strip()
            if not text:
                continue

            boxes = layout[page_num]["boxes"]
            index = field_config["box"]
            if index >= len(boxes):
                unresolved.append(field_name)
                continue
            box = boxes[index]

            # Boxes only one line tall get centred single-line treatment;
            # the tall comment boxes get wrapped paragraphs.
            if box.height < 24:
                fits = _draw_single_line(page, box, " ".join(text.split()))
            else:
                fits = _draw_wrapped(page, box, text)

            if not fits:
                overflowed.append(field_name)

        # Anything that spilled has to continue on an attachment, so tick page 1's
        # "I have provided supporting information ... attached to this SEE" box —
        # unless the caller has taken a position on it either way.
        if overflowed and form_data.get("supporting_info_attached") is None:
            checks = layout[0]["checks"]
            if checks:
                _draw_tick(doc[0], checks[0])

        doc.save(str(output_path))
        doc.close()

        return {
            "success": True,
            "overflowed_fields": overflowed,
            "unresolved_fields": unresolved,
            "template_layout_changed": template_changed,
        }

    except (OSError, RuntimeError, ValueError) as e:
        # Narrow on purpose: a failure to open or write the template is an
        # operational problem to report, but a TypeError in the field mapping is
        # a bug and must not be dressed up as one.
        record_document_error("fill_see_pdf", SEE_TEMPLATE_PATH.name, type(e).__name__, str(e))
        return {"success": False, "error": str(e)}
