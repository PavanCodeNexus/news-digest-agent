"""
Phase 3 (v6): Poster Generator — editorial redesign

Visual identity (deliberately not the generic "cream background + colored
bars + Arial" default):
  - Ink-navy on warm paper instead of black-on-cream
  - Three type roles: Georgia (serif display/headlines), Segoe UI (body),
    Consolas (tracked-out mono for labels, dates, tags, story numbers)
  - ONE accent color (muted amber), used only for the Critical badge and
    story numbering — not a different hue per section
  - Each section gets a small line-art icon instead of a solid color bar
  - Masthead styled like an actual newspaper nameplate: tracked eyebrow
    line with edition number, serif wordmark, double hairline rule

Both posters keep the same fixed section slots as before:
    World -> India -> Business & Economy -> Sports -> Technology -> Crime & Justice
"""

import os
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from image_fetcher import fetch_image_from_url, fetch_image_for_query

CANVAS_WIDTH = 1080
MARGIN = 44
HEADER_HEIGHT = 152
FOOTER_HEIGHT = 56
SECTION_HEADER_HEIGHT = 44
SECTION_GAP_AFTER = 20
EMPTY_SECTION_HEIGHT = 34

SECTIONS = ["World", "India", "Business & Economy", "Sports", "Technology", "Crime & Justice"]

# --- Disciplined palette: paper + ink + ONE accent, not a rainbow ---
PAPER = (247, 245, 239)
INK = (28, 34, 48)
ACCENT = (181, 121, 46)
MUTED = (114, 108, 97)
HAIRLINE = (218, 211, 194)
PLACEHOLDER_BG = (223, 217, 203)

# --- Three type roles (Windows-native; fall back gracefully elsewhere) ---
FONT_DISPLAY_BOLD = [
    "C:/Windows/Fonts/georgiab.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONT_DISPLAY_REGULAR = [
    "C:/Windows/Fonts/georgia.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_BODY_REGULAR = [
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_MONO_REGULAR = [
    "C:/Windows/Fonts/consola.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_MONO_BOLD = [
    "C:/Windows/Fonts/consolab.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _load_font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------
# Tracked (letter-spaced) text — used for all-caps labels, dates,
# tags, and the masthead eyebrow, giving them an editorial feel
# instead of plain cramped capitals.
# ---------------------------------------------------------------

def _tracked_width(draw, text, font, tracking):
    total = 0
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=font)
        total += (bbox[2] - bbox[0]) + tracking
    return max(total - tracking, 0)


def _tracked_text(draw, x, y, text, font, fill, tracking=3):
    cx = x
    for ch in text:
        draw.text((cx, y), ch, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), ch, font=font)
        cx += (bbox[2] - bbox[0]) + tracking
    return cx - x


def _wrap_and_truncate(draw, text, font, max_width, max_lines):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) == max_lines:
        rejoined = " ".join(lines)
        if rejoined != text:
            last = lines[-1]
            while draw.textbbox((0, 0), last + "...", font=font)[2] > max_width and len(last) > 3:
                last = last[:-1]
            lines[-1] = last.rstrip() + "..."
    return lines


def _placeholder_image(size, label):
    img = Image.new("RGB", size, PLACEHOLDER_BG)
    draw = ImageDraw.Draw(img)
    font = _load_font(FONT_BODY_REGULAR, 15)
    lines = _wrap_and_truncate(draw, label, font, size[0] - 16, max_lines=2)
    total_h = len(lines) * 19
    y = (size[1] - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (size[0] - (bbox[2] - bbox[0])) / 2
        draw.text((x, y), line, font=font, fill=(130, 124, 112))
        y += 19
    return img


def _get_story_image(article, size):
    img = fetch_image_from_url(article.get("image_url"), size=size)
    if img is not None:
        return img
    headline_words = re.sub(r"[^\w\s]", "", article.get("title", "")).split()[:5]
    query = " ".join(headline_words) or article.get("category", "news")
    img = fetch_image_for_query(query, size=size)
    if img is not None:
        return img
    return _placeholder_image(size, article.get("category", "News"))


# ---------------------------------------------------------------
# Section icons — small line-art marks (not a color-block system).
# Each is drawn in plain INK, ~26x26, consistent stroke.
# ---------------------------------------------------------------

def _icon_world(draw, x, y, s, color):
    draw.ellipse([x, y, x + s, y + s], outline=color, width=2)
    cx, cy = x + s / 2, y + s / 2
    draw.line([(cx, y + 1), (cx, y + s - 1)], fill=color, width=1)
    draw.ellipse([x + s * 0.12, cy - s * 0.30, x + s * 0.88, cy + s * 0.30], outline=color, width=1)


def _icon_india(draw, x, y, s, color):
    # simplified map-pin (generic location mark, not any national symbol)
    head_bottom = y + s * 0.62
    draw.ellipse([x + s * 0.12, y, x + s * 0.88, head_bottom], outline=color, width=2)
    cx = x + s / 2
    left = (x + s * 0.24, head_bottom - s * 0.10)
    right = (x + s * 0.76, head_bottom - s * 0.10)
    tip = (cx, y + s)
    draw.line([left, tip], fill=color, width=2)
    draw.line([right, tip], fill=color, width=2)
    r = s * 0.08
    draw.ellipse([cx - r, y + s * 0.30 - r, cx + r, y + s * 0.30 + r], fill=color)


def _icon_business(draw, x, y, s, color):
    bar_w = s * 0.20
    gap = s * 0.12
    heights = [s * 0.35, s * 0.62, s * 0.92]
    bx = x
    for h in heights:
        draw.rectangle([bx, y + s - h, bx + bar_w, y + s], fill=color)
        bx += bar_w + gap


def _icon_sports(draw, x, y, s, color):
    draw.ellipse([x, y, x + s, y + s], outline=color, width=2)
    draw.arc([x + s * 0.05, y + s * 0.30, x + s * 0.95, y + s * 1.05], start=200, end=340, fill=color, width=1)
    draw.arc([x + s * 0.05, y - s * 0.05, x + s * 0.95, y + s * 0.70], start=20, end=160, fill=color, width=1)


def _icon_technology(draw, x, y, s, color):
    pad = s * 0.20
    draw.rounded_rectangle([x + pad, y + pad, x + s - pad, y + s - pad], radius=3, outline=color, width=2)
    for t in (0.30, 0.70):
        ty = y + s * t
        draw.line([(x, ty), (x + pad, ty)], fill=color, width=2)
        draw.line([(x + s - pad, ty), (x + s, ty)], fill=color, width=2)
        tx = x + s * t
        draw.line([(tx, y), (tx, y + pad)], fill=color, width=2)
        draw.line([(tx, y + s - pad), (tx, y + s)], fill=color, width=2)


def _icon_crime(draw, x, y, s, color):
    cx = x + s / 2
    draw.line([(cx, y + 2), (cx, y + s - 2)], fill=color, width=2)
    bar_y = y + s * 0.22
    draw.line([(x + 1, bar_y), (x + s - 1, bar_y)], fill=color, width=2)
    r = s * 0.13
    for arm_x in (x + s * 0.10, x + s - s * 0.10):
        draw.line([(cx, bar_y), (arm_x, bar_y + s * 0.30)], fill=color, width=1)
        draw.ellipse([arm_x - r, bar_y + s * 0.30, arm_x + r, bar_y + s * 0.30 + r * 1.6], outline=color, width=1)
    draw.line([(x + s * 0.30, y + s - 2), (x + s * 0.70, y + s - 2)], fill=color, width=2)


SECTION_ICONS = {
    "World": _icon_world,
    "India": _icon_india,
    "Business & Economy": _icon_business,
    "Sports": _icon_sports,
    "Technology": _icon_technology,
    "Crime & Justice": _icon_crime,
}


def _draw_importance_badge(draw, x, y, importance, font_mono):
    label = importance.upper()
    text_w = _tracked_width(draw, label, font_mono, 2)
    box_h = font_mono.size + 8
    if importance == "Critical":
        draw.rectangle([x, y, x + text_w + 16, y + box_h], fill=INK)
        _tracked_text(draw, x + 8, y + 4, label, font_mono, PAPER, tracking=2)
        return text_w + 16
    elif importance == "Important":
        draw.rectangle([x, y, x + text_w + 16, y + box_h], outline=INK, width=1)
        _tracked_text(draw, x + 8, y + 4, label, font_mono, INK, tracking=2)
        return text_w + 16
    else:
        _tracked_text(draw, x, y + 4, label, font_mono, MUTED, tracking=2)
        return text_w


def _group_by_section(articles):
    section_lookup = {s.lower(): s for s in SECTIONS}
    grouped = {s: [] for s in SECTIONS}
    for a in articles:
        cat = (a.get("category") or "").strip().lower()
        matched = section_lookup.get(cat, "World")
        grouped[matched].append(a)

    priority = {"Critical": 0, "Important": 1, "Routine": 2}
    for s in grouped:
        grouped[s].sort(key=lambda a: priority.get(a.get("importance"), 3))
    return grouped


# ---------------------------------------------------------------
# Masthead — styled like an actual newspaper nameplate: tracked
# eyebrow (edition number + date), serif wordmark, double rule.
# ---------------------------------------------------------------

def _draw_masthead(draw, title, subtitle_right):
    font_eyebrow = _load_font(FONT_MONO_REGULAR, 13)
    font_wordmark = _load_font(FONT_DISPLAY_BOLD, 44)

    now = datetime.now()
    edition = f"VOL. {now.strftime('%Y')}  ·  NO. {now.strftime('%j')}  ·  BENGALURU"
    _tracked_text(draw, MARGIN, 28, edition, font_eyebrow, MUTED, tracking=2)

    date_str = now.strftime("%A, %d %B").upper()
    date_w = _tracked_width(draw, date_str, font_eyebrow, 2)
    _tracked_text(draw, CANVAS_WIDTH - MARGIN - date_w, 28, date_str, font_eyebrow, MUTED, tracking=2)

    draw.text((MARGIN, 54), title, font=font_wordmark, fill=INK)

    if subtitle_right:
        font_sub = _load_font(FONT_MONO_REGULAR, 13)
        sub_w = _tracked_width(draw, subtitle_right, font_sub, 2)
        _tracked_text(draw, CANVAS_WIDTH - MARGIN - sub_w, 100, subtitle_right, font_sub, ACCENT, tracking=2)

    rule_y = 118
    draw.line([(MARGIN, rule_y), (CANVAS_WIDTH - MARGIN, rule_y)], fill=INK, width=2)
    draw.line([(MARGIN, rule_y + 4), (CANVAS_WIDTH - MARGIN, rule_y + 4)], fill=HAIRLINE, width=1)


def _draw_section_header(draw, y, section_name, count, font_name, font_mono):
    icon_size = 26
    icon_fn = SECTION_ICONS.get(section_name)
    if icon_fn:
        icon_fn(draw, MARGIN, y, icon_size, INK)

    name_x = MARGIN + icon_size + 14
    draw.text((name_x, y - 3), section_name, font=font_name, fill=INK)
    name_bbox = draw.textbbox((name_x, y - 3), section_name, font=font_name)
    name_right = name_bbox[2] + 16

    count_label = f"{count} STORY" if count == 1 else f"{count} STORIES"
    count_w = _tracked_width(draw, count_label, font_mono, 2)
    count_x = CANVAS_WIDTH - MARGIN - count_w
    _tracked_text(draw, count_x, y + 5, count_label, font_mono, MUTED, tracking=2)

    rule_y = y + icon_size - 8
    if count_x - 14 > name_right:
        draw.line([(name_right, rule_y), (count_x - 14, rule_y)], fill=HAIRLINE, width=1)


def _draw_footer(draw, canvas_width, total_height):
    font_mono = _load_font(FONT_MONO_REGULAR, 12)
    rule_y = total_height - FOOTER_HEIGHT + 6
    draw.line([(MARGIN, rule_y), (canvas_width - MARGIN, rule_y)], fill=HAIRLINE, width=1)

    line1 = "SOURCES — GNEWS · GUARDIAN · PIB · THE HINDU · REUTERS · WSJ · TOI · INDIAN EXPRESS"
    line2 = "IMAGES — ORIGINAL SOURCE / PEXELS"
    w1 = _tracked_width(draw, line1, font_mono, 1)
    w2 = _tracked_width(draw, line2, font_mono, 1)
    _tracked_text(draw, (canvas_width - w1) / 2, rule_y + 14, line1, font_mono, MUTED, tracking=1)
    _tracked_text(draw, (canvas_width - w2) / 2, rule_y + 32, line2, font_mono, MUTED, tracking=1)


# ============================================================
# Poster 1: Important Digest — sectioned, single column, WITH
# images, top stories per section, numbered within each section.
# ============================================================

def generate_important_digest(articles, output_path=None, stories_per_section=2):
    grouped = _group_by_section(articles)

    font_section_name = _load_font(FONT_DISPLAY_BOLD, 22)
    font_mono = _load_font(FONT_MONO_REGULAR, 13)
    font_mono_bold = _load_font(FONT_MONO_BOLD, 13)
    font_number = _load_font(FONT_MONO_BOLD, 17)
    font_headline = _load_font(FONT_DISPLAY_BOLD, 22)
    font_summary = _load_font(FONT_BODY_REGULAR, 16)
    font_empty = _load_font(FONT_BODY_REGULAR, 15)

    thumb_size = (296, 168)
    number_col_width = 40
    text_x_offset = number_col_width + thumb_size[0] + 18
    content_width = CANVAS_WIDTH - (2 * MARGIN)
    text_width = content_width - text_x_offset
    row_gap = 24

    dummy_img = Image.new("RGB", (10, 10))
    dummy_draw = ImageDraw.Draw(dummy_img)

    total_height = HEADER_HEIGHT + 26
    section_plans = []
    for section in SECTIONS:
        stories = grouped[section][:stories_per_section]
        total_height += SECTION_HEADER_HEIGHT + row_gap
        if not stories:
            total_height += EMPTY_SECTION_HEIGHT + row_gap
            section_plans.append((section, []))
            continue

        row_plan = []
        for a in stories:
            headline_lines = _wrap_and_truncate(dummy_draw, a["title"], font_headline, text_width, max_lines=2)
            summary_lines = _wrap_and_truncate(dummy_draw, a.get("ai_summary", ""), font_summary, text_width, max_lines=3)
            text_block_height = 26 + len(headline_lines) * 27 + len(summary_lines) * 21
            row_height = max(thumb_size[1], text_block_height)
            row_plan.append((a, row_height))
            total_height += row_height + row_gap
        section_plans.append((section, row_plan))
        total_height += SECTION_GAP_AFTER

    total_height += FOOTER_HEIGHT

    img = Image.new("RGB", (CANVAS_WIDTH, total_height), PAPER)
    draw = ImageDraw.Draw(img)
    total_stories = sum(len(rows) for _, rows in section_plans)
    _draw_masthead(draw, "DAILY CURRENT AFFAIRS", f"{total_stories} TOP STORIES")

    y = HEADER_HEIGHT + 26
    for section, row_plan in section_plans:
        _draw_section_header(draw, y, section, len(row_plan), font_section_name, font_mono)
        y += SECTION_HEADER_HEIGHT + row_gap

        if not row_plan:
            draw.text((MARGIN + 40, y), "No major updates in this section today.", font=font_empty, fill=MUTED)
            y += EMPTY_SECTION_HEIGHT + row_gap
            continue

        for idx, (a, row_height) in enumerate(row_plan, start=1):
            num_label = f"{idx:02d}"
            _tracked_text(draw, MARGIN, y, num_label, font_number, ACCENT, tracking=1)

            photo_x = MARGIN + number_col_width
            photo = _get_story_image(a, thumb_size)
            img.paste(photo, (photo_x, y))

            text_x = MARGIN + text_x_offset
            importance = a.get("importance", "Important")
            _draw_importance_badge(draw, text_x, y, importance, font_mono_bold)

            ty = y + 26
            for line in _wrap_and_truncate(draw, a["title"], font_headline, text_width, max_lines=2):
                draw.text((text_x, ty), line, font=font_headline, fill=INK)
                ty += 27

            summary = a.get("ai_summary", "")
            if summary:
                for line in _wrap_and_truncate(draw, summary, font_summary, text_width, max_lines=3):
                    draw.text((text_x, ty), line, font=font_summary, fill=MUTED)
                    ty += 21

            y += row_height + row_gap

        y += SECTION_GAP_AFTER

    _draw_footer(draw, CANVAS_WIDTH, total_height)

    if output_path is None:
        os.makedirs("posters", exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = os.path.join("posters", f"important_digest_{timestamp_str}.png")

    img.save(output_path)
    print(f"[Poster] Important Digest saved to {output_path}")
    return output_path


# ============================================================
# Poster 2: Full Digest — sectioned, ALL stories, text-only,
# 2-column sub-grid within each section.
# ============================================================

def generate_full_digest(articles, output_path=None):
    grouped = _group_by_section(articles)

    font_section_name = _load_font(FONT_DISPLAY_BOLD, 22)
    font_mono = _load_font(FONT_MONO_REGULAR, 12)
    font_headline = _load_font(FONT_DISPLAY_BOLD, 17)
    font_summary = _load_font(FONT_BODY_REGULAR, 14)
    font_empty = _load_font(FONT_BODY_REGULAR, 14)

    num_columns = 2
    col_gap = 32
    row_gap = 20
    content_width = CANVAS_WIDTH - (2 * MARGIN)
    col_width = (content_width - (col_gap * (num_columns - 1))) // num_columns

    dummy_img = Image.new("RGB", (10, 10))
    dummy_draw = ImageDraw.Draw(dummy_img)

    total_height = HEADER_HEIGHT + 26
    section_plans = []

    for section in SECTIONS:
        stories = grouped[section]
        total_height += SECTION_HEADER_HEIGHT + row_gap

        if not stories:
            section_plans.append((section, EMPTY_SECTION_HEIGHT, []))
            total_height += EMPTY_SECTION_HEIGHT + SECTION_GAP_AFTER
            continue

        col_current_y = [0] * num_columns
        placements = []
        for a in stories:
            headline_lines = _wrap_and_truncate(dummy_draw, a["title"], font_headline, col_width, max_lines=2)
            summary_lines = _wrap_and_truncate(dummy_draw, a.get("ai_summary", ""), font_summary, col_width, max_lines=2)
            h = 22 + len(headline_lines) * 21 + len(summary_lines) * 18
            col = col_current_y.index(min(col_current_y))
            placements.append((a, col, col_current_y[col], h))
            col_current_y[col] += h + row_gap

        section_height = max(col_current_y)
        section_plans.append((section, section_height, placements))
        total_height += section_height + SECTION_GAP_AFTER

    total_height += FOOTER_HEIGHT

    img = Image.new("RGB", (CANVAS_WIDTH, total_height), PAPER)
    draw = ImageDraw.Draw(img)
    total_stories = sum(len(p) for _, _, p in section_plans)
    _draw_masthead(draw, "FULL NEWS DIGEST", f"{total_stories} STORIES")

    y = HEADER_HEIGHT + 26
    for section, section_height, placements in section_plans:
        _draw_section_header(draw, y, section, len(placements), font_section_name, font_mono)
        y += SECTION_HEADER_HEIGHT + row_gap

        if not placements:
            draw.text((MARGIN + 40, y), "No major updates in this section today.", font=font_empty, fill=MUTED)
            y += EMPTY_SECTION_HEIGHT + SECTION_GAP_AFTER
            continue

        section_top_y = y
        for a, col, y_offset, h in placements:
            x = MARGIN + col * (col_width + col_gap)
            item_y = section_top_y + y_offset

            importance = a.get("importance", "Routine")
            _draw_importance_badge(draw, x, item_y, importance, font_mono)

            ty = item_y + 20
            for line in _wrap_and_truncate(draw, a["title"], font_headline, col_width, max_lines=2):
                draw.text((x, ty), line, font=font_headline, fill=INK)
                ty += 21

            summary = a.get("ai_summary", "")
            if summary:
                for line in _wrap_and_truncate(draw, summary, font_summary, col_width, max_lines=2):
                    draw.text((x, ty), line, font=font_summary, fill=MUTED)
                    ty += 18

        y += section_height + SECTION_GAP_AFTER

    _draw_footer(draw, CANVAS_WIDTH, total_height)

    if output_path is None:
        os.makedirs("posters", exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = os.path.join("posters", f"full_digest_{timestamp_str}.png")

    img.save(output_path)
    print(f"[Poster] Full Digest saved to {output_path}")
    return output_path
