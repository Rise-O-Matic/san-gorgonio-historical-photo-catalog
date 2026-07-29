#!/usr/bin/env python3
"""Build the editable four-era timeline ramp used by the Beaumont mural."""

from __future__ import annotations

import html
import json
import math
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MILESTONES_PATH = ROOT / "data" / "timeline-milestones.json"
CATALOG_PATH = ROOT / "data" / "catalog.json"
OUTPUTS = (
    ROOT / "data" / "design-assets" / "timeline-mural-ramp.svg",
    ROOT / "site" / "assets" / "timeline-mural-ramp.svg",
)

WIDTH = 356.0  # 29 ft 8 in; one SVG unit equals one inch.
HEIGHT = 120.0
DOCUMENT_SCALE = 10
ANGLE_DEGREES = 5.0
SLOPE = math.tan(math.radians(ANGLE_DEGREES))
X_START = 28.0
X_END = 328.0
Y_START = 32.0

CARD_WIDTH = 13.6
CARD_HALF = CARD_WIDTH / 2
COPY_LEFT = -5.95
MODULE_FILL = "#FEFBF5"
PHOTO_MATTE_FILL = "#FDFBF5"
SHADOW_FILL = "#0B1618"
SHADOW_OPACITY = 0.20
HEADLINE_TOP = -8.10
HEADLINE_HEIGHT = 5.40
HEADLINE_RADIUS = 0.22
HEADLINE_SHADOW_OFFSET = 0.35
YEAR_BASELINE = -6.55
RULE_TOP = -5.75
RULE_WIDTH = 3.20
RULE_HEIGHT = 0.12
HEADLINE_BASELINE = -4.82
HEADLINE_LINE_HEIGHT = 0.88
LOWER_PANEL_TOP = 2.40
LOWER_PANEL_HEIGHT = 17.32
LOWER_PANEL_BOTTOM = LOWER_PANEL_TOP + LOWER_PANEL_HEIGHT
LOWER_PANEL_RADIUS = 0.40
LOWER_SHADOW_OFFSET = 0.46
ACCENT_HEIGHT = 0.56
PHOTO_LEFT = -5.95
PHOTO_TOP = 3.85
PHOTO_WIDTH = 11.90
PHOTO_HEIGHT = 9.90
CAPTION_BASELINE = 15.04
CAPTION_LINE_HEIGHT = 0.82
PHOTO_TILE_CENTER_OFFSET = (LOWER_PANEL_TOP + LOWER_PANEL_BOTTOM) / 2
ERA_LABEL_TOP = -19.50
ERA_LABEL_HEIGHT = 5.40

ERAS = (
    {
        "id": "era-1-homeland-rancho",
        "start": 1,
        "end": 2,
        "name": "Homeland & Rancho Beginnings",
        "range": "TIME IMMEMORIAL–1845",
        "color": "#15424A",
        "label_width": 50.0,
    },
    {
        "id": "era-2-railroad-town",
        "start": 3,
        "end": 10,
        "name": "Reservation, Railroad & Town",
        "range": "1876–EARLY 1900S",
        "color": "#494638",
        "label_width": 76.0,
    },
    {
        "id": "era-3-civic-orchard",
        "start": 11,
        "end": 16,
        "name": "Civic Life & Orchard Boom",
        "range": "1907–1914",
        "color": "#9A6857",
        "label_width": 68.0,
    },
    {
        "id": "era-4-modern-beaumont",
        "start": 17,
        "end": 20,
        "name": "Library Growth & Modern Beaumont",
        "range": "1965–2011",
        "color": "#C4A15E",
        "label_width": 62.0,
    },
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def point_for(position: int, count: int) -> tuple[float, float]:
    x = X_START + ((position - 1) / (count - 1)) * (X_END - X_START)
    y = Y_START + (x - X_START) * SLOPE
    return x, y


def top_rounded_bar_path(*, x: float, y: float, width: float, height: float, radius: float) -> str:
    right = x + width
    return (
        f"M {x + radius:.2f} {y:.2f} "
        f"H {right - radius:.2f} "
        f"Q {right:.2f} {y:.2f} {right:.2f} {y + radius:.2f} "
        f"V {y + height:.2f} H {x:.2f} V {y + radius:.2f} "
        f"Q {x:.2f} {y:.2f} {x + radius:.2f} {y:.2f} Z"
    )


def wrapped_tspans(
    text: str,
    *,
    x: float,
    y: float,
    width: int,
    line_height: float,
    max_lines: int,
    class_name: str | None = None,
) -> list[str]:
    lines = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .") + "…"
    class_attr = f' class="{class_name}"' if class_name else ""
    return [
        f'        <tspan x="{x:.2f}" y="{y + index * line_height:.2f}"{class_attr}>{esc(line)}</tspan>'
        for index, line in enumerate(lines)
    ]


def era_for(position: int) -> dict[str, object]:
    for era in ERAS:
        if int(era["start"]) <= position <= int(era["end"]):
            return era
    raise ValueError(f"No era defined for position {position}")


def load_events() -> list[dict[str, object]]:
    milestone_data = json.loads(MILESTONES_PATH.read_text(encoding="utf-8"))
    catalog_data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    records = {record["id"]: record for record in catalog_data["records"]}
    events: list[dict[str, object]] = []
    for milestone in sorted(milestone_data["milestones"], key=lambda item: item["position"]):
        record = records.get(milestone["record_id"])
        if record is None:
            raise ValueError(f"Missing catalog record {milestone['record_id']}")
        events.append({**milestone, "photo_title": record["title"]})
    if len(events) != 20:
        raise ValueError(f"Expected 20 timeline events, found {len(events)}")
    expected = list(range(1, 21))
    actual = [int(event["position"]) for event in events]
    if actual != expected:
        raise ValueError(f"Timeline positions are not contiguous: {actual}")
    return events


def build_svg(events: list[dict[str, object]]) -> str:
    points = {position: point_for(position, len(events)) for position in range(1, len(events) + 1)}
    out: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" data-scale="1:{DOCUMENT_SCALE}" data-full-size="{WIDTH:g}in x {HEIGHT:g}in" width="{WIDTH / DOCUMENT_SCALE:g}in" height="{HEIGHT / DOCUMENT_SCALE:g}in" viewBox="0 0 {WIDTH:g} {HEIGHT:g}" role="img" aria-labelledby="title desc">',
        '  <title id="title">Beaumont and San Gorgonio Pass four-era mural timeline</title>',
        f'  <desc id="desc">An editable 1:{DOCUMENT_SCALE}-scale, {ANGLE_DEGREES:g}-degree timeline for twenty approved historical events, styled from the visible artwork in timeline-module-master-v2. Each event has a serif year and headline above the line and a unified photo-caption matte below it. The line is divided into four eras.</desc>',
        '  <metadata>',
        f'    Production scale is 1:{DOCUMENT_SCALE}; enlarge the placed art to {DOCUMENT_SCALE * 100}% for the {WIDTH:g}in by {HEIGHT:g}in mural. The viewBox retains full-size inch coordinates.',
        f'    The timeline descends {ANGLE_DEGREES:g} degrees from left to right. All headline, photo and caption tiles remain level like escalator steps.',
        f'    Every photo-caption module center is {PHOTO_TILE_CENTER_OFFSET:.2f} full-size inches vertically below the line.',
        '    Visible styling is derived from timeline-module-master-v2 artwork; its written spec annotations were not used.',
        '    Photos are intentionally omitted. Replace the solid matte inside each group named photo-placeholder-XX in Adobe Illustrator.',
        '  </metadata>',
        '  <defs>',
        '    <style><![CDATA[',
        "      text { font-family: Georgia-Bold, Georgia, serif; font-weight: 700; }",
        '      .era-range { font-size: 1.10px; }',
        '      .era-name { font-size: 0.78px; fill: #17363C; }',
        '      .event-date { font-size: 1.55px; }',
        '      .event-date-long { font-size: 1.00px; }',
        '      .event-headline { font-size: 0.78px; fill: #17363C; }',
        '      .photo-title { font-size: 0.62px; fill: #2E2E2E; }',
        '    ]]></style>',
        '  </defs>',
        f'  <g id="timeline-ramp" data-angle="{ANGLE_DEGREES:g}-degrees" data-direction="down-left-to-right">',
        f'    <path id="timeline-underlay" d="M {X_START:.2f} {Y_START:.2f} L {X_END:.2f} {point_for(20, 20)[1]:.2f}" fill="none" stroke="#12191A" stroke-width="1.65" stroke-linecap="round"/>',
        '    <g id="era-segments">',
    ]

    for era in ERAS:
        start = int(era["start"])
        end = int(era["end"])
        if start == 1:
            x1 = X_START
        else:
            x1 = (points[start - 1][0] + points[start][0]) / 2
        if end == len(events):
            x2 = X_END
        else:
            x2 = (points[end][0] + points[end + 1][0]) / 2
        y1 = Y_START + (x1 - X_START) * SLOPE
        y2 = Y_START + (x2 - X_START) * SLOPE
        out.append(
            f'      <path id="{era["id"]}-line" d="M {x1:.2f} {y1:.2f} L {x2:.2f} {y2:.2f}" fill="none" stroke="{era["color"]}" stroke-width="1.05" stroke-linecap="butt"/>'
        )
    out.extend(['    </g>', '    <g id="era-labels">'])

    for era in ERAS:
        start_x, _ = points[int(era["start"])]
        end_x, _ = points[int(era["end"])]
        center_x = (start_x + end_x) / 2
        center_y = Y_START + (center_x - X_START) * SLOPE
        label_width = float(era["label_width"])
        out.extend(
            [
                f'      <g id="{era["id"]}-label" transform="translate({center_x:.2f} {center_y:.2f})">',
                f'        <rect x="{-label_width / 2:.2f}" y="{ERA_LABEL_TOP + HEADLINE_SHADOW_OFFSET:.2f}" width="{label_width:.2f}" height="{ERA_LABEL_HEIGHT:.2f}" rx="{HEADLINE_RADIUS:.2f}" fill="{SHADOW_FILL}" opacity="{SHADOW_OPACITY:.2f}"/>',
                f'        <rect x="{-label_width / 2:.2f}" y="{ERA_LABEL_TOP:.2f}" width="{label_width:.2f}" height="{ERA_LABEL_HEIGHT:.2f}" rx="{HEADLINE_RADIUS:.2f}" fill="{MODULE_FILL}"/>',
                f'        <text x="{-label_width / 2 + 0.85:.2f}" y="{ERA_LABEL_TOP + 1.55:.2f}" class="era-range" fill="{era["color"]}">{esc(era["range"])}</text>',
                f'        <rect x="{-label_width / 2 + 0.85:.2f}" y="{ERA_LABEL_TOP + 2.35:.2f}" width="{RULE_WIDTH:.2f}" height="{RULE_HEIGHT:.2f}" fill="{era["color"]}"/>',
                f'        <text x="{-label_width / 2 + 0.85:.2f}" y="{ERA_LABEL_TOP + 3.78:.2f}" class="era-name">{esc(era["name"])}</text>',
                '      </g>',
            ]
        )

    out.extend(['    </g>', f'    <g id="event-complexes" data-photo-tile-center-offset="{PHOTO_TILE_CENTER_OFFSET:.2f}in">'])

    for event in events:
        position = int(event["position"])
        x, y = points[position]
        era = era_for(position)
        color = str(era["color"])
        number = f"{position:02d}"
        event_id = f'event-{number}-{str(event["reference_number"]).lower()}'
        date_length = len(str(event["date"]))
        if date_length > 16:
            date_class = "event-date event-date-long"
        else:
            date_class = "event-date"
        out.extend(
            [
                f'      <g id="{event_id}" data-position="{number}" data-reference="{esc(event["reference_number"])}" data-record-id="{esc(event["record_id"])}" data-era="{esc(era["id"])}" transform="translate({x:.2f} {y:.2f})">',
                f'        <line id="event-stem-up-{number}" x1="0" y1="-1.20" x2="0" y2="{HEADLINE_TOP + HEADLINE_HEIGHT:.2f}" stroke="{color}" stroke-width="0.22"/>',
                f'        <line id="event-stem-down-{number}" x1="0" y1="1.20" x2="0" y2="{LOWER_PANEL_TOP:.2f}" stroke="{color}" stroke-width="0.22"/>',
                f'        <g id="milestone-headline-{number}">',
                f'          <rect x="{-CARD_HALF:.2f}" y="{HEADLINE_TOP + HEADLINE_SHADOW_OFFSET:.2f}" width="{CARD_WIDTH:.2f}" height="{HEADLINE_HEIGHT:.2f}" rx="{HEADLINE_RADIUS:.2f}" fill="{SHADOW_FILL}" opacity="{SHADOW_OPACITY:.2f}"/>',
                f'          <rect x="{-CARD_HALF:.2f}" y="{HEADLINE_TOP:.2f}" width="{CARD_WIDTH:.2f}" height="{HEADLINE_HEIGHT:.2f}" rx="{HEADLINE_RADIUS:.2f}" fill="{MODULE_FILL}"/>',
                f'          <text x="{COPY_LEFT:.2f}" y="{YEAR_BASELINE:.2f}" class="{date_class}" fill="{color}">{esc(event["date"])}</text>',
                f'          <rect id="milestone-rule-{number}" x="{COPY_LEFT:.2f}" y="{RULE_TOP:.2f}" width="{RULE_WIDTH:.2f}" height="{RULE_HEIGHT:.2f}" fill="{color}"/>',
                f'          <text aria-label="{esc(event["headline"])}">',
            ]
        )
        out.extend(
            wrapped_tspans(
                str(event["headline"]),
                x=COPY_LEFT,
                y=HEADLINE_BASELINE,
                width=28,
                line_height=HEADLINE_LINE_HEIGHT,
                max_lines=3,
                class_name="event-headline",
            )
        )
        out.extend(
            [
                '          </text>',
                '        </g>',
                f'        <g id="photo-caption-module-{number}">',
                f'          <rect x="{-CARD_HALF:.2f}" y="{LOWER_PANEL_TOP + LOWER_SHADOW_OFFSET:.2f}" width="{CARD_WIDTH:.2f}" height="{LOWER_PANEL_HEIGHT:.2f}" rx="{LOWER_PANEL_RADIUS:.2f}" fill="{SHADOW_FILL}" opacity="{SHADOW_OPACITY:.2f}"/>',
                f'          <rect x="{-CARD_HALF:.2f}" y="{LOWER_PANEL_TOP:.2f}" width="{CARD_WIDTH:.2f}" height="{LOWER_PANEL_HEIGHT:.2f}" rx="{LOWER_PANEL_RADIUS:.2f}" fill="{MODULE_FILL}"/>',
                f'          <path id="era-accent-{number}" d="{top_rounded_bar_path(x=-CARD_HALF, y=LOWER_PANEL_TOP, width=CARD_WIDTH, height=ACCENT_HEIGHT, radius=LOWER_PANEL_RADIUS)}" fill="{color}"/>',
                f'          <g id="photo-placeholder-{number}" data-replace-with-photo="true">',
                f'            <rect id="photo-matte-{number}" x="{PHOTO_LEFT:.2f}" y="{PHOTO_TOP:.2f}" width="{PHOTO_WIDTH:.2f}" height="{PHOTO_HEIGHT:.2f}" rx="{LOWER_PANEL_RADIUS:.2f}" fill="{PHOTO_MATTE_FILL}"/>',
                '          </g>',
                f'          <g id="caption-placeholder-{number}" data-position="{number}" data-reference="{esc(event["reference_number"])}">',
                f'          <text aria-label="{esc(event["photo_title"])}">',
            ]
        )
        out.extend(
            wrapped_tspans(
                str(event["photo_title"]),
                x=COPY_LEFT,
                y=CAPTION_BASELINE,
                width=33,
                line_height=CAPTION_LINE_HEIGHT,
                max_lines=3,
                class_name="photo-title",
            )
        )
        out.extend(
            [
                '          </text>',
                '          </g>',
                '        </g>',
                '      </g>',
            ]
        )

    out.extend(['    </g>', '    <g id="event-dots">'])
    for event in events:
        position = int(event["position"])
        x, y = points[position]
        era = era_for(position)
        color = str(era["color"])
        number = f"{position:02d}"
        out.extend(
            [
                f'      <g id="event-dot-{number}" data-position="{number}" data-reference="{esc(event["reference_number"])}">',
                f'        <circle cx="{x:.2f}" cy="{y:.2f}" r="1.12" fill="#F8F4EC" stroke="#12191A" stroke-width="0.22"/>',
                f'        <circle cx="{x:.2f}" cy="{y:.2f}" r="0.70" fill="{color}"/>',
                '      </g>',
            ]
        )
    out.extend(['    </g>', '  </g>', '</svg>', ''])
    return "\n".join(out)


def main() -> None:
    events = load_events()
    svg = build_svg(events)
    for output in OUTPUTS:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(svg, encoding="utf-8", newline="\n")
        print(output)


if __name__ == "__main__":
    main()
