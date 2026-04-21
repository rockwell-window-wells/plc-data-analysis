"""
id_cards.py

ID card generation logic, ported from id_methods.py.

All intermediate files (QR codes, card PNGs) are written to a temporary
directory that is cleaned up automatically. The final PDF is returned as
bytes so the Dash app can send it to the browser without writing to disk.

Card layout (4 per page, 2x2):
    TL  TR
    BL  BR

For operator cards, lead pages and assistant pages are interleaved.
Within each assistant page, cards are swapped left-right within each
column pair so they align correctly when printed double-sided on the
short edge:
    Lead   page: [A, B, C, D] -> TL, TR, BL, BR
    Assist page: [B, A, D, C] -> TL, TR, BL, BR

Dependencies:
    pip install pillow qrcode fpdf2
"""

import io
import os
import tempfile
import datetime as dt

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import qrcode
from fpdf import FPDF, XPos, YPos


# ---------------------------------------------------------------------------
# Card dimensions and colors -- preserved from id_methods.py
# ---------------------------------------------------------------------------

# Colors per prefix
PREFIX_COLORS = {
    "10": (255, 64,  64),   # Lead -- red
    "11": (97,  171, 255),  # Assistant -- blue
    "30": (209, 153, 255),  # Purple -- purple
    "31": (236, 232, 26),   # Bag -- yellow
}
WHITE_FALLBACK = (250, 250, 250)

# Card type labels per prefix
PREFIX_LABELS = {
    "10": "Lead",
    "11": "Assistant",
    "30": "Purple",
    "31": "Bag",
}

# PDF page layout -- preserved exactly from IDPDF in id_methods.py
PAGE_W  = 210   # mm (A4)
PAGE_H  = 297
CARD_W  = 71    # mm
CARD_H  = 113.6

MARGIN  = 0
BLEED   = 50    # pixels on card image


# ---------------------------------------------------------------------------
# ID string helpers
# ---------------------------------------------------------------------------

def format_id_string(prefix: int, employee_number: int) -> str:
    """
    Combine a 2-digit prefix and a 1-3 digit employee number into a
    5-character string, e.g. prefix=10, number=69 -> "10069".
    """
    return str(prefix) + str(employee_number).zfill(3)


# ---------------------------------------------------------------------------
# QR code generation (in-memory)
# ---------------------------------------------------------------------------

def generate_qr_image(id_string: str) -> Image.Image:
    """Generate a QR code PIL image for the given id_string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(id_string)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


# ---------------------------------------------------------------------------
# Card image generation
# Ported directly from generate_idcard() in id_methods.py.
# Accepts a PIL Image as the template rather than a file path.
# ---------------------------------------------------------------------------

def generate_card_image(
    template: Image.Image,
    id_string: str,
    item_type: str,
    employee_name: str | None,
    font_path: str,
) -> Image.Image:
    """
    Generate one ID card PIL image.

    Parameters
    ----------
    template      : White-background portrait template (PIL Image).
    id_string     : Full 5-digit ID string, e.g. "10069".
    item_type     : Role label, e.g. "Lead" or "Assistant".
    employee_name : Name printed on the card, or None for equipment cards.
    font_path     : Path to a TrueType font file.

    Returns
    -------
    PIL Image of the completed card.
    """
    prefix = id_string[:2]
    color  = PREFIX_COLORS.get(prefix, WHITE_FALLBACK)

    # Colour the white areas of the template
    card = template.copy().convert("RGBA")
    data = np.array(card)
    r, g, b, a = data.T
    white = (r == 255) & (g == 255) & (b == 255)
    data[..., :3][white.T] = color
    card = Image.fromarray(data).convert("RGB")

    W, H = card.size

    # Generate and place QR code
    qr_img   = generate_qr_image(id_string)
    qr_w, qr_h = qr_img.size

    # Scale QR to fit within card width minus bleed
    max_qr_w = W - 2 * BLEED
    factor = 1
    while (factor + 1) * qr_w <= max_qr_w:
        factor += 1
    qr_img = qr_img.resize((factor * qr_w, factor * qr_h))
    qr_w, qr_h = qr_img.size

    border = (W - qr_w) // 2 - BLEED
    left   = BLEED + border
    top    = H - border - BLEED - qr_h
    card.paste(qr_img, (left, top, left + qr_w, top + qr_h))

    # Draw text
    draw = ImageDraw.Draw(card)
    if prefix != "11":
        draw.rectangle((BLEED, BLEED, W - BLEED, H - BLEED), outline="black")

    def draw_centered(text, y_offset, fontsize=75):
        font = ImageFont.truetype(font_path, size=fontsize)
        # Shrink font until text fits
        while draw.textlength(text, font=font) >= (W - 2 * BLEED - 10) and fontsize > 10:
            fontsize -= 5
            font = ImageFont.truetype(font_path, size=fontsize)
        w = draw.textlength(text, font=font)
        draw.text(((W - w) / 2, y_offset), text, font=font, fill="black")

    section = H - W  # vertical space above the square portion
    if employee_name:
        draw_centered(employee_name, section / 6 + BLEED)
    draw_centered(item_type,  section / 2 + BLEED)
    draw_centered(id_string,  5 * section / 6 + BLEED)

    return card


# ---------------------------------------------------------------------------
# PDF assembly
# Ported from IDPDF and generate_IDPDF in id_methods.py.
# Works entirely from a list of in-memory PIL Images.
# ---------------------------------------------------------------------------

def _card_positions():
    """
    Return the (x, y) top-left corner of each of the 4 card slots on an A4
    page, in the order TL, TR, BL, BR. Matches the calculation in
    IDPDF.page_body() exactly.
    """
    wcc = MARGIN + (PAGE_W / 2 - MARGIN) / 2   # horizontal center of each half
    hcc = MARGIN + (PAGE_H / 2 - MARGIN) / 2   # vertical center of each half
    TLx = wcc - CARD_W / 2
    TLy = hcc - CARD_H / 2
    TRx = PAGE_W - wcc - CARD_W / 2
    TRy = TLy
    BLx = TLx
    BLy = PAGE_H - hcc - CARD_H / 2
    BRx = TRx
    BRy = BLy
    return [(TLx, TLy), (TRx, TRy), (BLx, BLy), (BRx, BRy)]


def _build_pages(groups: list[list]) -> list[list]:
    """
    Pad each group to exactly 4 slots, substituting None for blank slots.
    Mirrors the chunker + pad logic from id_methods.py.
    """
    pages = []
    for group in groups:
        n = len(group)
        padded = group + [None] * (4 - n)
        pages.append(padded)
    return pages


def _chunker(seq, size):
    for pos in range(0, len(seq), size):
        yield seq[pos:pos + size]


def _reorder_assist(group):
    """
    Swap cards within each column pair so the assistant page aligns with
    the lead page when printed double-sided on the short edge.
    Matches the reorder logic in unify_IDcard_lists() exactly.

    group is a list of up to 4 items (None = blank).
    """
    a, b, c, d = (group + [None] * 4)[:4]
    n = sum(1 for x in group if x is not None)
    if n == 4:
        return [b, a, d, c]
    elif n == 3:
        return [b, a, None, c]
    elif n == 2:
        return [b, a, None, None]
    else:  # n == 1
        return [None, a, None, None]


def _write_page(pdf, card_images_or_none, tmp_dir, page_num):
    """Write one page to the PDF. card_images_or_none is a list of 4 items,
    each either a PIL Image or None (blank slot)."""
    positions = _card_positions()
    pdf.add_page()

    for (x, y), img in zip(positions, card_images_or_none):
        if img is None:
            continue
        # Save card to temp PNG, add to PDF, then clean up
        tmp_path = os.path.join(tmp_dir, f"card_{page_num}_{x:.0f}_{y:.0f}.png")
        img.save(tmp_path, format="PNG")
        pdf.image(tmp_path, x=x, y=y, w=CARD_W)
        os.unlink(tmp_path)


class _IDPDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 5, f"Page {self.page_no()}", align="C")


def generate_operator_pdf(
    employee_numbers: list[int],
    names: dict[int, str],
    template: Image.Image,
    font_path: str,
) -> bytes:
    """
    Generate a double-sided operator ID card PDF as bytes.

    Parameters
    ----------
    employee_numbers : List of 3-digit employee numbers to include.
    names            : Dict mapping employee_number -> name string.
    template         : White portrait template PIL Image.
    font_path        : Path to a TrueType font file.

    Returns
    -------
    Raw PDF bytes suitable for dcc.send_bytes().
    """
    lead_cards   = []
    assist_cards = []

    for emp_num in employee_numbers:
        name = names.get(emp_num)

        lead_id   = format_id_string(10, emp_num)
        assist_id = format_id_string(11, emp_num)

        lead_cards.append(
            generate_card_image(template, lead_id,   "Lead",      name, font_path)
        )
        assist_cards.append(
            generate_card_image(template, assist_id, "Assistant", name, font_path)
        )

    # Chunk into groups of 4
    lead_groups   = list(_chunker(lead_cards,   4))
    assist_groups = list(_chunker(assist_cards, 4))

    pdf = _IDPDF()
    pdf.set_margins(0, 0, 0)

    with tempfile.TemporaryDirectory() as tmp_dir:
        for page_idx, (lg, ag) in enumerate(zip(lead_groups, assist_groups)):
            # Lead page: TL, TR, BL, BR order
            lead_page = (lg + [None] * 4)[:4]
            # Assist page: reordered for double-sided alignment
            assist_page = _reorder_assist(ag)

            _write_page(pdf, lead_page,   tmp_dir, page_idx * 2)
            _write_page(pdf, assist_page, tmp_dir, page_idx * 2 + 1)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Database helpers for number selection
# ---------------------------------------------------------------------------

def get_available_numbers(conn) -> list[int]:
    """
    Return all employee numbers in 1-999 that are currently available --
    either never assigned, or previously assigned but now inactive
    (active_to IS NOT NULL).

    Numbers where active_to IS NULL are currently in use and not available.
    Number 0 is reserved (means no operator clocked in) and excluded.
    """
    import sqlite3
    cursor = conn.cursor()

    # Numbers currently in active use
    cursor.execute("""
        SELECT DISTINCT employee_number FROM operators
        WHERE active_to IS NULL
    """)
    in_use = {row[0] for row in cursor.fetchall()}

    return [n for n in range(1, 1000) if n not in in_use]


def get_active_operators(conn) -> list[dict]:
    """
    Return all currently active operators as a list of dicts with keys:
    id, employee_number, name, active_from, shift.
    """
    import sqlite3
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, employee_number, name, active_from, shift
        FROM operators
        WHERE active_to IS NULL
        ORDER BY name ASC
    """)
    cols = ["id", "employee_number", "name", "active_from", "shift"]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def add_operator(conn, employee_number: int, name: str,
                 active_from: str, shift: str) -> int:
    """
    Insert a new operator row. Returns the new row id.
    Raises ValueError if the number is currently in active use.
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM operators
        WHERE employee_number = ? AND active_to IS NULL
    """, (employee_number,))
    if cursor.fetchone():
        raise ValueError(
            f"Employee number {employee_number} is currently in use."
        )

    cursor.execute("""
        INSERT INTO operators (employee_number, name, active_from, shift)
        VALUES (?, ?, ?, ?)
    """, (employee_number, name, active_from, shift))
    conn.commit()
    return cursor.lastrowid


def retire_operator(conn, operator_id: int, active_to: str):
    """
    Set active_to on an operator row, freeing their number for reuse.
    Raises ValueError if the operator is already retired.
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT active_to FROM operators WHERE id = ?
    """, (operator_id,))
    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"No operator found with id {operator_id}.")
    if row[0] is not None:
        raise ValueError(f"Operator id {operator_id} is already retired.")

    cursor.execute("""
        UPDATE operators SET active_to = ? WHERE id = ?
    """, (active_to, operator_id))
    conn.commit()
