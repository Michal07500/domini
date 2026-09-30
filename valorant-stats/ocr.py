"""EXPERIMENTÁLNE: čítanie kreditov z obrazovky pomocou OCR.

Program si urobí snímku malého výrezu obrazovky (tam, kde hra ukazuje kredity)
a Tesseract z nej prečíta číslo. Do hry nijako nezasahuje – je to ako screenshot.

Potrebuje:  pip install mss pillow pytesseract
a program Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
"""

import os
import re

try:
    import mss
    import pytesseract
    from PIL import Image, ImageOps
    MISSING = None
except ImportError as error:
    MISSING = error.name


_checked = {}


def available(tesseract_cmd=None):
    if tesseract_cmd in _checked:
        return _checked[tesseract_cmd]
    _checked[tesseract_cmd] = result = _check(tesseract_cmd)
    return result


def _check(tesseract_cmd):
    if MISSING:
        return False, f"Chýba knižnica '{MISSING}' (pip install mss pillow pytesseract)."
    if tesseract_cmd and os.path.exists(tesseract_cmd):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        return False, "Nenašiel sa program Tesseract OCR – nainštaluj ho a nastav cestu v Nastaveniach."
    return True, "OCR pripravené."


def grab(region):
    with (getattr(mss, "MSS", None) or mss.mss)() as screen:
        shot = screen.grab({"left": region[0], "top": region[1], "width": region[2], "height": region[3]})
        return Image.frombytes("RGB", shot.size, shot.rgb)


def read_number(image):
    """Z obrázka s číslom (napr. kredity) vráti int alebo None."""
    gray = ImageOps.grayscale(image)
    gray = gray.resize((gray.width * 3, gray.height * 3))
    # Kredity sú svetlé na tmavom pozadí – obrátime na tmavé písmo na bielom #
    bw = gray.point(lambda v: 0 if v > 150 else 255)
    text = pytesseract.image_to_string(bw, config="--psm 7 -c tessedit_char_whitelist=0123456789")
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    value = int(digits)
    return value if 0 <= value <= 9000 else None


def read_credits(region):
    return read_number(grab(region))
