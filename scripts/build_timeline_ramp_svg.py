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
ANGLE_DEGREES = 10.0
SLOPE = math.tan(math.radians(ANGLE_DEGREES))
X_START = 28.0
X_END = 328.0
Y_START = 32.0

CARD_WIDTH = 13.6
CARD_HALF = CARD_WIDTH / 2

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
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH:g}in" height="{HEIGHT:g}in" viewBox="0 0 {WIDTH:g} {HEIGHT:g}" role="img" aria-labelledby="title desc">',
        '  <title id="title">Beaumont and San Gorgonio Pass four-era mural timeline</title>',
        f'  <desc id="desc">An editable, full-size {ANGLE_DEGREES:g}-degree timeline for twenty approved historical events. Each event has a dot, milestone headline, photo placeholder and caption placeholder. The line is divided into four eras.</desc>',
        '  <metadata>',
        '    One SVG unit equals one inch. Artboard: 29 ft 8 in by 10 ft. The timeline descends 10 degrees from left to right.',
        '    Photos are intentionally omitted. Replace each group named photo-placeholder-XX in Adobe Illustrator.',
        '  </metadata>',
        '  <defs>',
        '    <style><![CDATA[',
        "      text { font-family: 'Libre Franklin', 'Franklin Gothic Book', Arial, sans-serif; }",
        "      .era-name { font-family: 'DM Serif Display', Georgia, serif; font-size: 1.10px; font-weight: 700; fill: #1D2729; }",
        '      .era-range { font-size: 0.62px; font-weight: 800; letter-spacing: 0.14px; fill: #665B4C; }',
        '      .event-date { font-size: 0.50px; font-weight: 800; letter-spacing: 0.10px; }',
        "      .event-headline { font-family: 'DM Serif Display', Georgia, serif; font-size: 0.66px; font-weight: 700; fill: #17363C; }",
        '      .photo-fpo { font-size: 0.58px; font-weight: 800; letter-spacing: 0.09px; fill: #6D675E; }',
        '      .photo-ref { font-size: 0.43px; font-weight: 700; letter-spacing: 0.06px; fill: #8A8276; }',
        '      .position { font-size: 0.47px; font-weight: 800; letter-spacing: 0.08px; }',
        "      .photo-title { font-family: 'DM Serif Display', Georgia, serif; font-size: 0.60px; font-weight: 700; fill: #222; }",
        '      .replace-note { font-size: 0.39px; font-style: italic; fill: #706A61; }',
        '    ]]></style>',
        '    <filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="160%">',
        '      <feDropShadow dx="0" dy="0.45" stdDeviation="0.55" flood-color="#0B1618" flood-opacity="0.30"/>',
        '    </filter>',
        '  </defs>',
        '  <g id="timeline-ramp" data-angle="10-degrees" data-direction="down-left-to-right">',
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
                f'      <g id="{era["id"]}-label" transform="translate({center_x:.2f} {center_y:.2f}) rotate({ANGLE_DEGREES:g})">',
                f'        <rect x="{-label_width / 2:.2f}" y="-18.20" width="{label_width:.2f}" height="4.75" rx="1.15" fill="#F8F4EC" stroke="{era["color"]}" stroke-width="0.22" filter="url(#soft-shadow)"/>',
                f'        <rect x="{-label_width / 2:.2f}" y="-18.20" width="{label_width:.2f}" height="0.55" rx="0.27" fill="{era["color"]}"/>',
                f'        <text x="0" y="-15.76" text-anchor="middle" class="era-name">{esc(era["name"])}</text>',
                f'        <text x="0" y="-14.45" text-anchor="middle" class="era-range">{esc(era["range"])}</text>',
                '      </g>',
            ]
        )

    out.extend(['    </g>', '    <g id="event-complexes">'])

    for event in events:
        position = int(event["position"])
        x, y = points[position]
        era = era_for(position)
        color = str(era["color"])
        number = f"{position:02d}"
        event_id = f'event-{number}-{str(event["reference_number"]).lower()}'
        out.extend(
            [
                f'      <g id="{event_id}" data-position="{number}" data-reference="{esc(event["reference_number"])}" data-record-id="{esc(event["record_id"])}" data-era="{esc(era["id"])}" transform="translate({x:.2f} {y:.2f}) rotate({ANGLE_DEGREES:g})">',
                f'        <g id="milestone-headline-{number}" filter="url(#soft-shadow)">',
                f'          <rect x="{-CARD_HALF:.2f}" y="-10.10" width="{CARD_WIDTH:.2f}" height="7.95" rx="0.62" fill="#F8F4EC" stroke="{color}" stroke-width="0.16"/>',
                f'          <rect x="{-CARD_HALF:.2f}" y="-10.10" width="{CARD_WIDTH:.2f}" height="0.50" rx="0.25" fill="{color}"/>',
                f'          <text x="{-CARD_HALF + 0.68:.2f}" y="-8.65" class="event-date" fill="{color}">{esc(event["date"])} · HISTORICAL MILESTONE</text>',
                f'          <text aria-label="{esc(event["headline"])}">',
            ]
        )
        out.extend(
            wrapped_tspans(
                str(event["headline"]),
                x=-CARD_HALF + 0.68,
                y=-7.28,
                width=34,
                line_height=0.82,
                max_lines=4,
                class_name="event-headline",
            )
        )
        out.extend(
            [
                '          </text>',
                '        </g>',
                f'        <g id="photo-placeholder-{number}">',
                f'          <rect x="{-CARD_HALF:.2f}" y="2.25" width="{CARD_WIDTH:.2f}" height="8.15" rx="0.32" fill="#E8E2D8" stroke="#1D282A" stroke-width="0.18" stroke-dasharray="0.52 0.34"/>',
                f'          <line x1="{-CARD_HALF + 0.50:.2f}" y1="2.75" x2="{CARD_HALF - 0.50:.2f}" y2="9.90" stroke="#B8B0A4" stroke-width="0.13"/>',
                f'          <line x1="{CARD_HALF - 0.50:.2f}" y1="2.75" x2="{-CARD_HALF + 0.50:.2f}" y2="9.90" stroke="#B8B0A4" stroke-width="0.13"/>',
                f'          <text x="0" y="5.94" text-anchor="middle" class="photo-fpo">PHOTO {number}</text>',
                f'          <text x="0" y="7.08" text-anchor="middle" class="photo-ref">{esc(event["reference_number"])}</text>',
                f'          <text x="0" y="8.22" text-anchor="middle" class="replace-note">Replace this group with the selected photograph</text>',
                '        </g>',
                f'        <g id="caption-placeholder-{number}">',
                f'          <rect x="{-CARD_HALF:.2f}" y="10.72" width="{CARD_WIDTH:.2f}" height="5.55" rx="0.30" fill="#FCFAF6" stroke="#D7C9B3" stroke-width="0.15"/>',
                f'          <rect x="{-CARD_HALF:.2f}" y="10.72" width="{CARD_WIDTH:.2f}" height="0.34" fill="{color}"/>',
                f'          <text x="{-CARD_HALF + 0.68:.2f}" y="12.06" class="position" fill="{color}">{number} · {esc(event["reference_number"])}</text>',
                f'          <text aria-label="{esc(event["photo_title"])}">',
            ]
        )
        out.extend(
            wrapped_tspans(
                str(event["photo_title"]),
                x=-CARD_HALF + 0.68,
                y=13.30,
                width=39,
                line_height=0.78,
                max_lines=3,
                class_name="photo-title",
            )
        )
        out.extend(
            [
                '          </text>',
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
