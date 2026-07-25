#!/usr/bin/env python3
"""Read-only historical image ingestion and static catalog generator.

The script never writes inside a configured source directory. All generated
artifacts are placed beneath the repository's data/ and site/ directories.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import ExifTags, Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".gif", ".bmp", ".heic", ".avif"}
DOCUMENT_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS
DATE_RE = re.compile(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)")
DECADE_RE = re.compile(r"(?<!\d)((?:18|19|20)\d0)s?(?!\d)", re.I)
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
GENERIC_TOKENS = {
    "img", "image", "photo", "photograph", "scan", "scanned", "copy", "final", "edit",
    "edited", "new", "old", "small", "large", "original", "version", "web", "tinified",
    "jpg", "jpeg", "png", "tif", "tiff", "unknown", "untitled", "historical", "photos"
}
EXIF_NAMES = {key: value for key, value in ExifTags.TAGS.items()}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path))).replace("\\", "/")


def is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def assert_safe_outputs(repo: Path, sources: list[dict[str, Any]], *outputs: Path) -> None:
    roots = [Path(item["path"]) for item in sources]
    for output in outputs:
        if not is_inside(output, repo):
            raise RuntimeError(f"Output must stay inside repository: {output}")
        for root in roots:
            if is_inside(output, root):
                raise RuntimeError(f"Refusing to write inside source: {output}")


def stable_id(prefix: str, value: str, length: int = 16) -> str:
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def hamming(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def bits_to_hex(bits: Iterable[bool]) -> str:
    value = 0
    count = 0
    for bit in bits:
        value = (value << 1) | int(bool(bit))
        count += 1
    return f"{value:0{math.ceil(count / 4)}x}"


def difference_hash(image: Image.Image) -> str:
    gray = ImageOps.grayscale(image).resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(gray.get_flattened_data() if hasattr(gray, "get_flattened_data") else gray.getdata())
    return bits_to_hex(pixels[row * 9 + col] > pixels[row * 9 + col + 1] for row in range(8) for col in range(8))


def average_hash(image: Image.Image) -> str:
    gray = ImageOps.grayscale(image).resize((8, 8), Image.Resampling.LANCZOS)
    pixels = list(gray.get_flattened_data() if hasattr(gray, "get_flattened_data") else gray.getdata())
    mean = sum(pixels) / len(pixels)
    return bits_to_hex(pixel >= mean for pixel in pixels)


def transformed_hashes(image: Image.Image) -> dict[str, str]:
    return {
        "normal": difference_hash(image),
        "rot90": difference_hash(image.rotate(90, expand=True)),
        "rot180": difference_hash(image.rotate(180, expand=True)),
        "rot270": difference_hash(image.rotate(270, expand=True)),
        "mirror": difference_hash(ImageOps.mirror(image)),
    }


def edge_sharpness(image: Image.Image) -> float:
    sample = ImageOps.grayscale(image)
    sample.thumbnail((900, 900), Image.Resampling.LANCZOS)
    edges = sample.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return round(float(stat.var[0]), 3)


def crop_hashes(image: Image.Image) -> list[str]:
    width, height = image.size
    values = []
    for fraction in (0.05, 0.1, 0.15):
        dx, dy = int(width * fraction), int(height * fraction)
        if width - 2 * dx > 20 and height - 2 * dy > 20:
            values.append(difference_hash(image.crop((dx, dy, width - dx, height - dy))))
    return values


def clean_exif(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[:2000]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (tuple, list)):
        return [clean_exif(item) for item in value]
    return str(value)[:2000]


def image_metadata(path: Path) -> tuple[dict[str, Any], Image.Image]:
    with Image.open(path) as source:
        source.load()
        image = ImageOps.exif_transpose(source).convert("RGB")
        raw_exif = source.getexif()
        exif = {EXIF_NAMES.get(key, str(key)): clean_exif(value) for key, value in raw_exif.items()}
        metadata = {
            "format": source.format or path.suffix.lstrip(".").upper(),
            "width": image.width,
            "height": image.height,
            "megapixels": round(image.width * image.height / 1_000_000, 2),
            "mode": source.mode,
            "frames": getattr(source, "n_frames", 1),
            "exif": exif,
            "sharpness_score": edge_sharpness(image),
            "dhash": difference_hash(image),
            "ahash": average_hash(image),
            "transform_hashes": transformed_hashes(image),
            "crop_hashes": crop_hashes(image),
        }
        return metadata, image


def pdf_metadata(path: Path) -> tuple[dict[str, Any], Image.Image]:
    try:
        import fitz  # PyMuPDF, optional
    except ImportError as exc:
        raise RuntimeError("PDF preview requires optional PyMuPDF") from exc
    document = fitz.open(path)
    if document.page_count < 1:
        raise RuntimeError("PDF has no pages")
    page = document.load_page(0)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    metadata = {
        "format": "PDF",
        "width": image.width,
        "height": image.height,
        "megapixels": round(image.width * image.height / 1_000_000, 2),
        "mode": "RGB",
        "frames": document.page_count,
        "exif": {"pdf_metadata": clean_exif(document.metadata)},
        "sharpness_score": edge_sharpness(image),
        "dhash": difference_hash(image),
        "ahash": average_hash(image),
        "transform_hashes": transformed_hashes(image),
        "crop_hashes": crop_hashes(image),
    }
    document.close()
    return metadata, image


def open_asset(path: Path) -> tuple[dict[str, Any], Image.Image]:
    if path.suffix.lower() == ".pdf":
        return pdf_metadata(path)
    if path.suffix.lower() in {".heic", ".avif"}:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError(f"{path.suffix.upper()} decode requires local FFmpeg")
        process = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "pipe:1"],
            capture_output=True, timeout=120, check=False
        )
        if process.returncode != 0 or not process.stdout:
            raise RuntimeError(f"FFmpeg could not decode {path.suffix}: {process.stderr.decode(errors='replace')[:500]}")
        with Image.open(io.BytesIO(process.stdout)) as decoded:
            decoded.load()
            image = ImageOps.exif_transpose(decoded).convert("RGB")
        metadata = {
            "format": path.suffix.lstrip(".").upper(), "width": image.width, "height": image.height,
            "megapixels": round(image.width * image.height / 1_000_000, 2), "mode": "RGB", "frames": 1,
            "exif": {}, "sharpness_score": edge_sharpness(image), "dhash": difference_hash(image),
            "ahash": average_hash(image), "transform_hashes": transformed_hashes(image), "crop_hashes": crop_hashes(image),
            "decoded_with": "ffmpeg"
        }
        return metadata, image
    return image_metadata(path)


def optimized_image(image: Image.Image, destination: Path, size: int, quality: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    rendered = image.copy()
    rendered.thumbnail((size, size), Image.Resampling.LANCZOS)
    rendered.save(destination, "JPEG", quality=quality, optimize=True, progressive=True)


def source_overlap(sources: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    active: list[dict[str, Any]] = []
    overlap: list[dict[str, str]] = []
    ordered = sorted(sources, key=lambda item: len(normalize_path(Path(item["path"]))))
    for source in ordered:
        path = Path(source["path"])
        parent = next((item for item in active if is_inside(path, Path(item["path"]))), None)
        if parent:
            overlap.append({"skipped_source": source["key"], "path": str(path), "covered_by": parent["key"]})
        else:
            active.append(source)
    return active, overlap


def inventory_sources(sources: list[dict[str, Any]]) -> tuple[list[tuple[Path, dict[str, Any]]], dict[str, Any]]:
    active, overlaps = source_overlap(sources)
    items: list[tuple[Path, dict[str, Any]]] = []
    report_sources = []
    seen_paths: set[str] = set()
    source_by_path = sorted(sources, key=lambda item: (item.get("priority", 0), len(normalize_path(Path(item["path"])))), reverse=True)

    for source in sources:
        root = Path(source["path"])
        report_sources.append({
            "key": source["key"], "path": str(root), "available": root.exists(),
            "scan_status": "nested-skip" if any(row["skipped_source"] == source["key"] for row in overlaps) else "active",
            "curated": bool(source.get("curated")), "priority": source.get("priority", 0),
        })

    for scan_source in active:
        root = Path(scan_source["path"])
        if not root.exists():
            continue
        iterator = root.rglob("*") if scan_source.get("recursive", True) else root.glob("*")
        for path in iterator:
            try:
                if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
            except OSError:
                continue
            normalized = normalize_path(path)
            if normalized in seen_paths:
                continue
            seen_paths.add(normalized)
            memberships = [item for item in source_by_path if is_inside(path, Path(item["path"]))]
            effective = memberships[0] if memberships else scan_source
            items.append((path, {
                "source_key": effective["key"],
                "source_priority": effective.get("priority", 0),
                "curated": any(item.get("curated") for item in memberships),
                "source_memberships": [item["key"] for item in memberships],
            }))
    items.sort(key=lambda pair: normalize_path(pair[0]))
    return items, {"sources": report_sources, "overlaps": overlaps, "unique_candidate_files": len(items)}


def find_tesseract() -> str | None:
    configured = os.environ.get("TESSERACT_CMD")
    candidates = [configured, shutil.which("tesseract"), r"C:\Program Files\Tesseract-OCR\tesseract.exe"]
    return next((item for item in candidates if item and Path(item).exists()), None)


def run_ocr(image_path: Path, tesseract: str | None) -> dict[str, Any]:
    if not tesseract:
        return {"status": "unavailable", "text": "", "engine": None, "confidence": None}
    try:
        result = subprocess.run(
            [tesseract, str(image_path), "stdout", "--psm", "11"],
            capture_output=True, text=True, timeout=90, check=False, encoding="utf-8", errors="replace"
        )
        text = re.sub(r"\s+", " ", result.stdout).strip()
        return {"status": "complete" if result.returncode == 0 else "failed", "text": text, "engine": "tesseract", "confidence": None, "error": result.stderr.strip()[:500]}
    except Exception as exc:
        return {"status": "failed", "text": "", "engine": "tesseract", "confidence": None, "error": str(exc)}


def filename_suggestions(path: Path, ocr_text: str) -> dict[str, Any]:
    raw = " ".join([path.stem, *path.parts[-4:-1]])
    years = sorted({int(value) for value in DATE_RE.findall(raw) if 1800 <= int(value) <= datetime.now().year})
    decades = sorted({int(value) for value in DECADE_RE.findall(raw)})
    tokens = [token for token in TOKEN_RE.findall(path.stem.replace("_", " ").replace("-", " ")) if token.lower() not in GENERIC_TOKENS and not token.isdigit()]
    title = " ".join(tokens).strip().title() or path.stem
    title = re.sub(r"\s+", " ", title)[:140]
    visible_text = ocr_text[:500]
    return {
        "title": title,
        "caption": "",
        "date_start": years[0] if len(years) == 1 else None,
        "date_end": years[-1] if years else None,
        "decade": decades[0] if len(decades) == 1 else (years[0] // 10 * 10 if len(years) == 1 else None),
        "locations": [], "people": [], "subjects": tokens[:12],
        "visible_text": visible_text,
        "search_terms": sorted({token.lower() for token in tokens})[:20],
        "confidence": "low",
        "review_note": "Machine suggestion from filename/folder/OCR only; verify before treating as fact."
    }


def read_sidecars(path: Path) -> list[dict[str, Any]]:
    facts = []
    for suffix in (".txt", ".md", ".json"):
        candidate = path.with_suffix(suffix)
        if not candidate.exists() or candidate == path:
            continue
        try:
            content = candidate.read_text(encoding="utf-8", errors="replace")[:20000]
            facts.append({"kind": "sidecar", "path": str(candidate), "value": content})
        except OSError as exc:
            facts.append({"kind": "sidecar-error", "path": str(candidate), "value": str(exc)})
    return facts


def collect_website_caption_index(sources: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for source in sources:
        caption_root = source.get("caption_root")
        if not caption_root or not Path(caption_root).exists():
            continue
        root = Path(caption_root)
        html_files = list(root.glob("*.html")) + list(root.glob("*.htm"))
        for page in html_files[:200]:
            try:
                content = page.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for match in re.finditer(r"<img\b[^>]*>", content, flags=re.I | re.S):
                tag = match.group(0)
                src_match = re.search(r"\bsrc=[\"']([^\"']+)", tag, flags=re.I)
                if not src_match:
                    continue
                filename = Path(src_match.group(1).split("?")[0]).name.lower()
                fields = []
                for name in ("alt", "title"):
                    field = re.search(rf"\b{name}=[\"']([^\"']*)", tag, flags=re.I)
                    if field and field.group(1).strip():
                        fields.append(html.unescape(field.group(1).strip()))
                if fields:
                    index[filename].append({"page": str(page), "caption": " | ".join(fields)})
    return index


def quality_label(score: float) -> tuple[str, float]:
    if score >= 450:
        return "sharp", 1.0
    if score >= 170:
        return "moderate", 0.75
    return "soft_or_damaged", 0.5


def print_metrics(width: int, height: int, quality_factor: float, crop_allowance: float) -> dict[str, Any]:
    usable_width = width * (1 - crop_allowance)
    usable_height = height * (1 - crop_allowance)
    effective_width = usable_width * quality_factor
    effective_height = usable_height * quality_factor
    levels = {}
    for ppi in (200, 150, 100, 50):
        levels[str(ppi)] = {
            "width_inches": round(effective_width / ppi, 1),
            "height_inches": round(effective_height / ppi, 1),
            "native_crop_width_inches": round(usable_width / ppi, 1),
            "native_crop_height_inches": round(usable_height / ppi, 1),
        }
    default = levels["100"]
    short_side = min(default["width_inches"], default["height_inches"])
    classification = "Production Ready" if short_side >= 16 else "Potentially Usable" if short_side >= 8 else "Reference Only"
    return {
        "crop_allowance_percent": round(crop_allowance * 100, 1),
        "quality_factor": quality_factor,
        "ppi": levels,
        "recommended": f"{default['width_inches']:g} × {default['height_inches']:g} in at 100 PPI",
        "classification": classification,
        "ai_upscaled_estimate": None,
    }


def pair_similarity(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any] | None:
    if left["sha256"] == right["sha256"]:
        return {"classification": "exact", "confidence": 1.0, "distance": 0, "reason": "Identical SHA-256"}
    lm, rm = left["image"], right["image"]
    aspect_left = lm["width"] / max(lm["height"], 1)
    aspect_right = rm["width"] / max(rm["height"], 1)
    aspect_delta = abs(math.log(max(aspect_left, 0.001) / max(aspect_right, 0.001)))
    normal_distance = hamming(lm["dhash"], rm["dhash"])
    transformed = min(
        (hamming(value, rm["dhash"]), name) for name, value in lm["transform_hashes"].items()
    )
    crop_distance = min(
        [hamming(value, rm["dhash"]) for value in lm["crop_hashes"]]
        + [hamming(value, lm["dhash"]) for value in rm["crop_hashes"]]
        + [64]
    )
    if normal_distance <= 5 and aspect_delta <= 0.035:
        return {"classification": "reencoded_or_resized", "confidence": round(1 - normal_distance / 20, 3), "distance": normal_distance, "reason": "Very close perceptual hash and aspect ratio"}
    if transformed[0] <= 7 and transformed[1] != "normal":
        return {"classification": "rotated_or_mirrored", "confidence": round(0.9 - transformed[0] / 30, 3), "distance": transformed[0], "reason": f"Close after {transformed[1]} transform"}
    if crop_distance <= 8 or (normal_distance <= 9 and aspect_delta <= 0.12):
        return {"classification": "cropped_or_reprocessed", "confidence": round(0.8 - min(crop_distance, normal_distance) / 40, 3), "distance": min(crop_distance, normal_distance), "reason": "Similar after crop/reprocessing comparison"}
    if normal_distance <= 13 and aspect_delta <= 0.2:
        return {"classification": "probable_match", "confidence": round(0.68 - normal_distance / 100, 3), "distance": normal_distance, "reason": "Perceptually similar; manual review required"}
    return None


class UnionFind:
    def __init__(self, keys: Iterable[str]):
        self.parent = {key: key for key in keys}

    def find(self, key: str) -> str:
        while self.parent[key] != key:
            self.parent[key] = self.parent[self.parent[key]]
            key = self.parent[key]
        return key

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def master_score(file: dict[str, Any]) -> float:
    image = file["image"]
    pixels = image["width"] * image["height"]
    completeness = 1.0
    compression = 1.0 if image["format"] in {"TIFF", "TIF", "PNG"} else 0.9
    curated_bonus = 1.05 if file["curated"] else 1.0
    return math.log10(max(pixels, 1)) * math.log10(max(image["sharpness_score"], 1) + 10) * completeness * compression * curated_bonus


def merge_record(group: list[dict[str, Any]], match_map: dict[tuple[str, str], dict[str, Any]], crop_allowance: float) -> dict[str, Any]:
    ordered = sorted(group, key=master_score, reverse=True)
    master = ordered[0]
    facts: list[dict[str, Any]] = []
    suggestions = []
    for item in ordered:
        facts.extend(item["facts"])
        suggestions.append({"file_id": item["file_id"], "suggestion": item["suggestions"]})
    title = next((item["suggestions"]["title"] for item in ordered if item["suggestions"]["title"]), "Untitled historical photograph")
    years = sorted({item["suggestions"]["date_start"] for item in ordered if item["suggestions"]["date_start"]})
    quality, factor = quality_label(master["image"]["sharpness_score"])
    record_seed = min(item["sha256"] for item in group)
    record_id = stable_id("img", record_seed)
    alternates = []
    for item in ordered[1:]:
        key = tuple(sorted((master["file_id"], item["file_id"])))
        alternates.append({"file_id": item["file_id"], "relationship": match_map.get(key, {}).get("classification", "grouped_version")})
    return {
        "id": record_id,
        "title": title,
        "caption": "",
        "attribution": "Unknown",
        "attribution_confidence": "unknown",
        "caption_source": "",
        "date": {"start": years[0] if years else None, "end": years[-1] if years else None, "display": str(years[0]) if len(years) == 1 else "Undated", "confidence": "low" if years else "unknown", "editable": True},
        "decade": years[0] // 10 * 10 if years else None,
        "locations": [], "people": [],
        "subjects": sorted({subject for item in ordered for subject in item["suggestions"]["subjects"]}),
        "visible_text": " | ".join(filter(None, (item["ocr"]["text"] for item in ordered)))[:1000],
        "search_terms": sorted({term for item in ordered for term in item["suggestions"]["search_terms"]}),
        "research_status": "Needs research",
        "rights_status": "Unclear",
        "rights_note": "Do not infer reuse rights from age; verify against the holding institution or rights statement.",
        "selected_default": any(item["curated"] for item in group),
        "curated": any(item["curated"] for item in group),
        "master_file_id": master["file_id"],
        "master_reason": "Highest composite of genuine pixel dimensions, measured edge detail, lossless-format preference, completeness, and curated priority; review visually before production.",
        "version_file_ids": [item["file_id"] for item in ordered],
        "alternates": alternates,
        "quality": {"label": quality, "factor": factor, "editable": True},
        "print_viability": print_metrics(master["image"]["width"], master["image"]["height"], factor, crop_allowance),
        "metadata_suggestions": suggestions,
        "facts": facts,
        "conflicts": [{"field": "date", "values": years, "needs_review": True}] if len(years) > 1 else [],
        "client": {"selected": any(item["curated"] for item in group), "comment": ""},
    }


def apply_editorial_overrides(records: list[dict[str, Any]], overrides_path: Path) -> int:
    """Overlay researched date ranges (and other reviewed fields) onto generated records.

    The pipeline never infers historical dates on its own beyond single explicit
    filename years, so records without an unambiguous year are emitted as
    "Undated". This maintained layer carries the results of manual research
    (filename/masthead/postmark annotations, institutional histories, and visual
    dating) so those verified ranges survive every rerun. Missing file: no-op.
    """
    if not overrides_path.exists():
        return 0
    try:
        doc = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    overrides = doc.get("overrides", {})
    applied = 0
    for record in records:
        entry = overrides.get(record["id"])
        if not entry:
            continue
        start, end = entry.get("date_start"), entry.get("date_end")
        record["date"] = {
            "start": start, "end": end,
            "display": entry.get("display", str(start) if start else "Undated"),
            "confidence": entry.get("confidence", "medium"),
            "editable": True, "source": "editorial_research",
            "basis": entry.get("basis", ""),
        }
        record["decade"] = (start // 10 * 10) if start else None
        if record.get("research_status") == "Needs research":
            record["research_status"] = "Date researched"
        applied += 1
    return applied


def apply_editorial_captions(records: list[dict[str, Any]], captions_path: Path) -> int:
    """Overlay researched captions and attributions onto generated records.

    The pipeline emits an empty caption and a default "Unknown" attribution for
    every record; it never invents descriptive text on its own. This maintained
    layer (data/editorial-captions.json) carries the results of manual research —
    captions and credit lines harvested from the San Gorgonio Pass Historical
    Society timeline, the Banning Library District / Calisphere collections, and
    the open web, plus descriptive captions written from the catalog's own
    subject/people/location/date facts where no published caption exists. Every
    record is captioned and attributed; attribution is honestly recorded as
    "Unknown" when no holder or creator can be established. Missing file: no-op.
    """
    if not captions_path.exists():
        return 0
    try:
        doc = json.loads(captions_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    entries = doc.get("captions", {})
    applied = 0
    for record in records:
        entry = entries.get(record["id"])
        if not entry:
            continue
        caption = (entry.get("caption") or "").strip()
        if caption:
            record["caption"] = caption
        attribution = (entry.get("attribution") or "").strip()
        if attribution:
            record["attribution"] = attribution
        record["attribution_confidence"] = entry.get("attribution_confidence", record.get("attribution_confidence", "unknown"))
        if entry.get("caption_source"):
            record["caption_source"] = entry["caption_source"]
        if entry.get("basis"):
            fact = {
                "field": "caption_basis", "value": entry["basis"],
                "source": "editorial_research", "confidence": "provided",
            }
            # Idempotent: this overlay is re-run on every apply_*.py pass, so an
            # unconditional append accumulates a duplicate caption_basis fact per run.
            facts = record.setdefault("facts", [])
            if fact not in facts:
                facts.append(fact)
        applied += 1
    return applied


def apply_editorial_research(records: list[dict[str, Any]], research_path: Path) -> int:
    """Overlay the deep-research layer onto generated records.

    data/editorial-research.json (merged from the per-batch JSON files under
    data/research-authored/ by scripts/author_research.py)
    carries what the caption and date layers cannot: corrected display titles,
    long descriptions, per-photo corrections logs, per-claim evidence links,
    rights findings, holding institutions with item URLs, pointers to
    better-than-archive masters, and open questions for the holding
    institutions. Records covered here are marked "Researched"; the pipeline
    itself never asserts any of this. Missing file: no-op.
    """
    if not research_path.exists():
        return 0
    try:
        doc = json.loads(research_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    entries = doc.get("entries", {})
    doc_manifest = doc.get("source_manifest", "")
    applied = 0
    for record in records:
        entry = entries.get(record["id"])
        if not entry:
            continue
        research = {
            key: entry[key]
            for key in ("select_position", "original_title", "description",
                        "corrections", "evidence", "holding", "best_master",
                        "open_questions", "researched")
            if entry.get(key) not in (None, [], "")
        }
        source_manifest = entry.get("source_manifest") or doc_manifest
        if source_manifest:
            research["source_manifest"] = source_manifest
        record["research"] = research
        if entry.get("title"):
            record["title"] = entry["title"]
        if entry.get("rights"):
            record["rights_note"] = entry["rights"]
        if entry.get("rights_status"):
            record["rights_status"] = entry["rights_status"]
        record["research_status"] = entry.get("research_status", "Researched")
        applied += 1
    return applied


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ingest(config_path: Path, repo: Path, skip_ocr: bool = False) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = repo / config.get("output_directory", "data")
    site = repo / config.get("site_directory", "site")
    thumbs = site / "assets" / "thumbs"
    previews = site / "assets" / "previews"
    assert_safe_outputs(repo, config["sources"], output, site, thumbs, previews)
    output.mkdir(parents=True, exist_ok=True)
    thumbs.mkdir(parents=True, exist_ok=True)
    previews.mkdir(parents=True, exist_ok=True)

    candidates, inventory = inventory_sources(config["sources"])
    caption_index = collect_website_caption_index(config["sources"])
    tesseract = None if skip_ocr else find_tesseract()
    files: list[dict[str, Any]] = []
    unreadable = []
    started = time.time()

    for number, (path, source) in enumerate(candidates, 1):
        normalized = normalize_path(path)
        file_id = stable_id("file", normalized)
        try:
            stat = path.stat()
            digest = sha256_file(path)
            metadata, image = open_asset(path)
            thumb_rel = f"assets/thumbs/{file_id}.jpg"
            preview_rel = f"assets/previews/{file_id}.jpg"
            optimized_image(image, site / thumb_rel, int(config.get("thumbnail_size", 560)), int(config.get("jpeg_quality", 84)))
            optimized_image(image, site / preview_rel, int(config.get("preview_size", 1600)), int(config.get("jpeg_quality", 84)))
            ocr = run_ocr(site / preview_rel, tesseract)
            suggestions = filename_suggestions(path, ocr["text"])
            facts = [
                {"field": "source_path", "value": str(path), "source": "filesystem", "confidence": "certain"},
                {"field": "filename", "value": path.name, "source": "filesystem", "confidence": "certain"},
            ]
            facts.extend({"field": "sidecar", "value": item["value"], "source": item["path"], "confidence": "provided"} for item in read_sidecars(path))
            for caption in caption_index.get(path.name.lower(), []):
                facts.append({"field": "website_caption", "value": caption["caption"], "source": caption["page"], "confidence": "provided"})
            file = {
                "file_id": file_id, "path": str(path), "filename": path.name,
                "extension": path.suffix.lower(), "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "modified_at_is_historical_date": False,
                "sha256": digest, **source, "image": metadata, "ocr": ocr,
                "suggestions": suggestions, "facts": facts,
                "thumbnail": thumb_rel, "preview": preview_rel,
            }
            files.append(file)
            if number % 25 == 0:
                print(f"Processed {number}/{len(candidates)}", flush=True)
        except (OSError, RuntimeError, UnidentifiedImageError, ValueError) as exc:
            placeholder_hint = "cloud-placeholder-or-unavailable-offline" if path.exists() and path.stat().st_size == 0 else "unreadable-or-unsupported"
            unreadable.append({"path": str(path), "filename": path.name, "source_key": source["source_key"], "reason": str(exc), "classification": placeholder_hint, "action": "Make available offline and rerun" if "placeholder" in placeholder_hint else "Inspect format/file integrity"})

    match_map: dict[tuple[str, str], dict[str, Any]] = {}
    review_pairs = []
    uf = UnionFind(item["file_id"] for item in files)
    for index, left in enumerate(files):
        for right in files[index + 1:]:
            match = pair_similarity(left, right)
            if not match:
                continue
            key = tuple(sorted((left["file_id"], right["file_id"])))
            match_map[key] = match
            row = {"left_file_id": left["file_id"], "right_file_id": right["file_id"], "left_path": left["path"], "right_path": right["path"], **match}
            review_pairs.append(row)
            if match["classification"] in {"exact", "reencoded_or_resized", "rotated_or_mirrored", "cropped_or_reprocessed"} and match["confidence"] >= 0.72:
                uf.union(left["file_id"], right["file_id"])

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in files:
        grouped[uf.find(item["file_id"])].append(item)
    crop_allowance = float(config.get("crop_allowance_percent", 10)) / 100
    records = [merge_record(group, match_map, crop_allowance) for group in grouped.values()]
    apply_editorial_overrides(records, repo / config.get("output_directory", "data") / "editorial-overrides.json")
    apply_editorial_captions(records, repo / config.get("output_directory", "data") / "editorial-captions.json")
    apply_editorial_research(records, repo / config.get("output_directory", "data") / "editorial-research.json")
    records.sort(key=lambda item: (item["date"]["start"] is None, item["date"]["start"] or 9999, item["title"].lower()))
    file_index = {item["file_id"]: item for item in files}
    for record in records:
        master = file_index[record["master_file_id"]]
        record["thumbnail"] = master["thumbnail"]
        record["preview"] = master["preview"]
        record["original_pixels"] = {"width": master["image"]["width"], "height": master["image"]["height"]}

    research_queue = []
    for record in records:
        researched = record.get("research_status") == "Researched"
        priority = 100 if record["curated"] else 40
        if record["print_viability"]["classification"] != "Production Ready":
            priority += 20
        if not record["date"]["start"]:
            priority += 10
        if researched:
            priority = 0
        research_queue.append({
            "record_id": record["id"], "title": record["title"], "priority": priority,
            "reason": "Researched — evidence-linked record in the catalog" if researched
            else ("Curated mural candidate" if record["curated"] else "Low native print viability or missing historical context"),
            "status": "Researched" if researched else "Queued", "search_terms": record["search_terms"],
            "candidate_sources": config.get("research_sources", []), "candidates": []
        })
    research_queue.sort(key=lambda item: (-item["priority"], item["title"]))

    counts = Counter(item["extension"] for item in files)
    duplicate_counts = Counter(item["classification"] for item in review_pairs)
    catalog = {
        "schema_version": "1.0.0", "generated_at": now_iso(), "project_title": config["project_title"],
        "settings": {"default_ppi": config.get("default_ppi", 100), "crop_allowance_percent": config.get("crop_allowance_percent", 10), "quality_factors": config.get("quality_factors", {})},
        "summary": {"candidate_files": len(candidates), "readable_files": len(files), "unreadable_files": len(unreadable), "historical_records": len(records), "curated_records": sum(item["curated"] for item in records), "selected_by_default": sum(item["selected_default"] for item in records), "formats": dict(sorted(counts.items())), "duplicate_pair_classes": dict(sorted(duplicate_counts.items())), "elapsed_seconds": round(time.time() - started, 2), "ocr_engine": tesseract},
        "records": records, "files": files,
    }
    json_dump(output / "catalog.json", catalog)
    json_dump(site / "data" / "catalog.json", catalog)
    json_dump(output / "research-queue.json", research_queue)
    json_dump(site / "data" / "research-queue.json", research_queue)
    candidate_reviews = {"schema_version": "1.0.0", "generated_at": now_iso(), "candidates": config.get("research_candidates", [])}
    json_dump(output / "candidate-reviews.json", candidate_reviews)
    json_dump(site / "data" / "candidate-reviews.json", candidate_reviews)
    inventory.update({"generated_at": now_iso(), "readable_files": len(files), "unreadable_files": len(unreadable), "formats": dict(sorted(counts.items()))})
    json_dump(output / "reports" / "inventory.json", inventory)
    json_dump(output / "reports" / "unreadable-files.json", unreadable)
    json_dump(output / "reports" / "duplicate-review.json", {"pairs": review_pairs})
    write_csv(output / "files.csv", [{**item, "width": item["image"]["width"], "height": item["image"]["height"], "format": item["image"]["format"]} for item in files], ["file_id", "path", "filename", "source_key", "source_priority", "curated", "sha256", "size_bytes", "format", "width", "height", "thumbnail", "preview"])
    write_csv(output / "catalog.csv", [{"id": item["id"], "title": item["title"], "caption": item.get("caption", ""), "attribution": item.get("attribution", "Unknown"), "attribution_confidence": item.get("attribution_confidence", "unknown"), "caption_source": item.get("caption_source", ""), "date_start": item["date"]["start"], "date_end": item["date"]["end"], "decade": item["decade"], "curated": item["curated"], "selected_default": item["selected_default"], "classification": item["print_viability"]["classification"], "recommended_print": item["print_viability"]["recommended"], "master_file_id": item["master_file_id"], "rights_status": item["rights_status"], "research_status": item["research_status"], "evidence_urls": "; ".join(evidence["url"] for evidence in (item.get("research") or {}).get("evidence", []) if evidence.get("url"))} for item in records], ["id", "title", "caption", "attribution", "attribution_confidence", "caption_source", "date_start", "date_end", "decade", "curated", "selected_default", "classification", "recommended_print", "master_file_id", "rights_status", "research_status", "evidence_urls"])
    write_csv(output / "reports" / "unreadable-files.csv", unreadable, ["path", "filename", "source_key", "reason", "classification", "action"])
    write_csv(output / "reports" / "duplicate-review.csv", review_pairs, ["classification", "confidence", "distance", "reason", "left_file_id", "right_file_id", "left_path", "right_path"])
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/catalog.config.json")
    parser.add_argument("--skip-ocr", action="store_true", help="Do not invoke Tesseract even if installed")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    config_path = (repo / args.config).resolve()
    catalog = ingest(config_path, repo, skip_ocr=args.skip_ocr)
    print(json.dumps(catalog["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
