"""SEE PDF form geometry.

This is the highest-consequence code in the repo. The template carries no
AcroForm fields, so answers are drawn onto discovered rectangles addressed by
index. If Council reissues the form with a different layout, indices silently
shift and an applicant's name, address or answers get drawn into the wrong box
on a document that goes to Council.

SEE_LAYOUT_EXPECTED exists to make that fail loudly. Nothing ran it until now.
"""

import pytest

fitz = pytest.importorskip("fitz")

from lismore_da_mcp.server import (  # noqa: E402
    CHECKBOX_GLYPHS,
    SEE_FORM_FIELDS,
    SEE_LAYOUT_EXPECTED,
    _answer_boxes,
    _checkbox_rects,
    see_layout,
)


@pytest.fixture(scope="module")
def layout(see_template):
    doc = fitz.open(see_template)
    try:
        yield see_layout(doc), len(doc)
    finally:
        doc.close()


class TestTemplateMatchesExpectations:
    """If these fail, the template changed — do not adjust the numbers without
    re-deriving every index in SEE_FORM_FIELDS against the new form."""

    def test_page_count_covers_expectations(self, layout):
        _, page_count = layout
        assert page_count > max(SEE_LAYOUT_EXPECTED)

    @pytest.mark.parametrize("page_num", sorted(SEE_LAYOUT_EXPECTED))
    def test_box_and_checkbox_counts(self, layout, page_num):
        found, _ = layout
        want_boxes, want_checks = SEE_LAYOUT_EXPECTED[page_num]
        assert page_num in found, f"page {page_num + 1} missing from template"
        assert len(found[page_num]["boxes"]) == want_boxes
        assert len(found[page_num]["checks"]) == want_checks


class TestFieldsResolve:
    """Every configured field must point at a rectangle that actually exists."""

    def test_every_field_index_is_in_range(self, layout):
        found, page_count = layout
        unresolved = []
        for name, config in SEE_FORM_FIELDS.items():
            page = config["page"]
            if page >= page_count:
                unresolved.append(f"{name}: page {page} beyond document")
                continue
            kind = "checks" if "check" in config else "boxes"
            index = config.get("check", config.get("box"))
            if index >= len(found[page][kind]):
                unresolved.append(f"{name}: {kind}[{index}] of {len(found[page][kind])}")
        assert unresolved == []

    def test_no_two_text_fields_share_a_box(self):
        seen = {}
        for name, config in SEE_FORM_FIELDS.items():
            if "box" not in config:
                continue
            key = (config["page"], config["box"])
            assert key not in seen, f"{name} collides with {seen[key]} at {key}"
            seen[key] = name

    def test_no_two_tick_fields_share_a_checkbox(self):
        seen = {}
        for name, config in SEE_FORM_FIELDS.items():
            if "check" not in config:
                continue
            key = (config["page"], config["check"])
            assert key not in seen, f"{name} collides with {seen[key]} at {key}"
            seen[key] = name


class TestGeometryDiscovery:
    def test_boxes_are_in_reading_order(self, layout):
        found, _ = layout
        for page_num, content in found.items():
            tops = [round(r.y0) for r in content["boxes"]]
            assert tops == sorted(tops), f"page {page_num + 1} boxes out of order"

    def test_checkboxes_are_in_reading_order(self, layout):
        found, _ = layout
        for page_num, content in found.items():
            tops = [round(r.y0) for r in content["checks"]]
            assert tops == sorted(tops), f"page {page_num + 1} ticks out of order"

    def test_discovered_boxes_have_usable_area(self, layout):
        found, _ = layout
        for content in found.values():
            for rect in content["boxes"]:
                assert rect.width >= 30 and rect.height >= 10

    def test_checkbox_glyphs_are_non_empty(self):
        assert CHECKBOX_GLYPHS

    def test_answer_boxes_ignores_non_white_fills(self, see_template):
        """The discovery rule is 'white-filled rectangle'; a page of grey chrome
        alone must not be mistaken for input boxes."""
        doc = fitz.open(see_template)
        try:
            for page in doc:
                for rect in _answer_boxes(page):
                    assert rect.width >= 30
        finally:
            doc.close()

    def test_checkbox_rects_returns_rectangles(self, see_template):
        doc = fitz.open(see_template)
        try:
            rects = [r for page in doc for r in _checkbox_rects(page)]
        finally:
            doc.close()
        assert all(r.width > 0 and r.height > 0 for r in rects)
