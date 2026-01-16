from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from datetime import datetime
import re

import json
import numpy as np
from easyocr import Reader
from PIL import Image, ImageGrab

IMAGE_PATH = Path("Can.jpg")
CROP_BOXES: Dict[str, Tuple[int, int, int, int]] = {
	"502": (257, 281, 394, 311),
	"505": (230, 595, 363, 626),
	"508": (534, 284, 671, 310),
	"574": (535, 593, 671, 627),
	"DATE_TIME": (1797, 1040, 1867, 1078),
}

READER = Reader(["en"], gpu=False)
DEFAULT_DATE_ORDER = "mdy"


def extract_text_from_image(image: Image.Image) -> List[Tuple[str, float]]:
	result = READER.readtext(np.array(image))
	texts: List[Tuple[str, float]] = []
	for _, text, confidence in result:
		if text:
			texts.append((text, confidence))
	return texts


def ocr_regions_from_image(image: Image.Image) -> Dict[str, List[Tuple[str, float]]]:
	responses: Dict[str, List[Tuple[str, float]]] = {}
	for label, crop_box in CROP_BOXES.items():
		crop = image.crop(crop_box)
		responses[label] = extract_text_from_image(crop)
	return responses


def ocr_regions_from_path(image_path: Path | str) -> Dict[str, List[Tuple[str, float]]]:
	with Image.open(image_path) as image:
		return ocr_regions_from_image(image)

def _get_clipboard_image() -> Image.Image:
	data = ImageGrab.grabclipboard()
	if isinstance(data, Image.Image):
		return data
	if isinstance(data, Iterable):
		first = next(iter(data), None)
		if first:
			with Image.open(first) as img:
				return img.copy()
	raise RuntimeError("Clipboard does not contain image data.")


def ocr_regions_from_clipboard() -> Dict[str, List[Tuple[str, float]]]:
	image = _get_clipboard_image()
	return ocr_regions_from_image(image)


def _normalize_datetime_text(text: str) -> str:
	return " ".join(text.split())


def _parse_datetime(text: str, date_order: str) -> datetime | None:
	normalized = _normalize_datetime_text(text)
	time_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", normalized)
	date_match = re.search(r"(\d{1,4}[/-]\d{1,2}[/-]\d{2,4})", normalized)
	if not time_match or not date_match:
		return None
	time_raw = time_match.group(1)
	date_raw = date_match.group(1).replace("-", "/")
	time_formats = ("%H:%M:%S", "%H:%M")
	date_formats = {
		"mdy": "%m/%d/%Y",
		"dmy": "%d/%m/%Y",
		"ymd": "%Y/%m/%d",
	}
	date_fmt = date_formats.get(date_order, date_formats[DEFAULT_DATE_ORDER])
	for time_fmt in time_formats:
		try:
			parsed_date = datetime.strptime(date_raw, date_fmt)
			parsed_time = datetime.strptime(time_raw, time_fmt)
			return parsed_date.replace(
				hour=parsed_time.hour,
				minute=parsed_time.minute,
				second=parsed_time.second,
			)
		except ValueError:
			continue
	return None


def _merge_datetime_entries(
	entries: List[Tuple[str, float]],
	date_order: str = DEFAULT_DATE_ORDER,
) -> List[Tuple[str, float]]:
	valid_entries = [(text.strip(), confidence) for text, confidence in entries if text.strip()]
	if not valid_entries:
		return []
	combined_text = " ".join(text for text, _ in valid_entries)
	parsed = _parse_datetime(combined_text, date_order)
	avg_confidence = sum(conf for _, conf in valid_entries) / len(valid_entries)
	if parsed is not None:
		formatted = parsed.strftime("%d/%m/%Y %H:%M:%S")
		return [(formatted, avg_confidence)]
	return [(combined_text, avg_confidence)]


def to_serializable(
	results: Dict[str, List[Tuple[str, float]]],
	date_order: str = DEFAULT_DATE_ORDER,
) -> Dict[str, List[Dict[str, float | str]]]:
	serializable: Dict[str, List[Dict[str, float | str]]] = {}
	for label, entries in results.items():
		if label == "DATE_TIME":
			from pathlib import Path
			import json

			from utils.ocr_utils import (
				DEFAULT_DATE_ORDER,
				ocr_regions_from_path,
				to_serializable,
			)

			IMAGE_PATH = Path("Can.jpg")


			def main() -> None:
				results = ocr_regions_from_path(IMAGE_PATH)
				print(
					json.dumps(
						to_serializable(results, date_order=DEFAULT_DATE_ORDER),
						ensure_ascii=False,
						indent=2,
					)
				)
