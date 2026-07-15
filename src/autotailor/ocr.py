import os
import cv2
import numpy as np
import pytesseract
from PIL import Image

def configure_tesseract(tessdata_dir_config=None):
    """
    Finds and sets TESSDATA_PREFIX for tesseract OCR.
    Checks config path, project directory, and fallback folders.
    """
    if tessdata_dir_config and os.path.exists(tessdata_dir_config):
        os.environ['TESSDATA_PREFIX'] = tessdata_dir_config
        return tessdata_dir_config

    # Find the root of the project relative to this file
    # src/autotailor/ocr.py -> src/autotailor -> src -> project_root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_tessdata = os.path.join(base_dir, "tessdata")
    if os.path.exists(project_tessdata):
        os.environ['TESSDATA_PREFIX'] = project_tessdata
        return project_tessdata

    fallback_dir = r"C:\AUTOMATIZATION\scantailor\tessdata"
    if os.path.exists(fallback_dir):
        os.environ['TESSDATA_PREFIX'] = fallback_dir
        return fallback_dir

    return None

def detect_rotation(img, rotation_keywords, ocr_language="ukr"):
    """
    Rotates a scaled-down binary version of the image in 0, 90, 180, and 270 degrees.
    Determines orientation based on keyword matches from rotation_keywords.
    """
    best_angle = 0
    max_matches = -1
    best_word_count = -1
    
    h, w = img.shape[:2]
    scale = 1600.0 / max(h, w)
    
    for angle in [0, 90, 180, 270]:
        if angle == 90:
            rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            rotated = cv2.rotate(img, cv2.ROTATE_180)
        elif angle == 270:
            rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            rotated = img
            
        rh, rw = rotated.shape[:2]
        small = cv2.resize(rotated, (int(rw * scale), int(rh * scale)))
        
        # Binarize to maximize OCR readability
        if len(small.shape) == 3:
            b_ch, g_ch, r_ch = cv2.split(small)
            gray = cv2.min(cv2.min(r_ch, g_ch), b_ch)
        else:
            gray = small
            
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 15)
        
        pil_img = Image.fromarray(binary)
        config = '--psm 11'
        try:
            text = pytesseract.image_to_string(pil_img, lang=ocr_language, config=config).lower()
            matches = sum(1 for kw in rotation_keywords if kw.lower() in text)
            word_count = len(text.split())
            if matches > max_matches or (matches == max_matches and word_count > best_word_count):
                max_matches = matches
                best_word_count = word_count
                best_angle = angle
        except Exception:
            pass
            
    if max_matches <= 0:
        return None
    return best_angle

def perform_ocr_verification(processed_img, checklist_words, ocr_language="ukr+eng"):
    """
    Performs full OCR and verifies if checklist keywords are present.
    """
    if len(processed_img.shape) == 3:
        pil_img = Image.fromarray(cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB))
    else:
        pil_img = Image.fromarray(processed_img)
        
    try:
        custom_config = '--psm 11'
        text = pytesseract.image_to_string(pil_img, lang=ocr_language, config=custom_config)
        text_lower = text.lower()
        
        chk_results = {}
        for word in checklist_words:
            chk_results[word] = word.lower() in text_lower
            
        found_count = sum(chk_results.values())
        char_count = len(text.strip())
        word_count = len(text.split())
        is_valid = found_count >= 1 or char_count > 100
        
        return text, chk_results, found_count, char_count, word_count, is_valid
    except Exception as e:
        return f"OCR Error: {e}", {}, 0, 0, 0, False
