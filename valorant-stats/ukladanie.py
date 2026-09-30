"""Ukladanie histórie zápasov, rozohraného zápasu a nastavení do JSON súborov."""

import json
import os

FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moje_data")
HISTORY_FILE = os.path.join(FOLDER, "historia.json")
CURRENT_FILE = os.path.join(FOLDER, "rozohrany_zapas.json")
SETTINGS_FILE = os.path.join(FOLDER, "nastavenia.json")

DEFAULT_SETTINGS = {
    "main_geometry": "1280x820+40+40",
    "overlay_geometry": None,
    "overlay_alpha": 0.88,
    "overlay_scale": 1.0,
    "overlay_visible": True,
    "ocr_region": None,
    "ocr_auto": False,
    "tesseract_cmd": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
}


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save(path, data):
    os.makedirs(FOLDER, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # bezpečné prepísanie – pri páde sa súbor nepokazí


def load_history():
    return _load(HISTORY_FILE, [])


def save_history(matches):
    _save(HISTORY_FILE, matches)


def load_current():
    return _load(CURRENT_FILE, None)


def save_current(match):
    if match is None:
        if os.path.exists(CURRENT_FILE):
            os.remove(CURRENT_FILE)
    else:
        _save(CURRENT_FILE, match)


def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    settings.update(_load(SETTINGS_FILE, {}))
    return settings


def save_settings(settings):
    _save(SETTINGS_FILE, settings)
