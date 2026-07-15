import os
import sys
import glob
import json
import argparse
import subprocess
import cv2
from PIL import Image, ExifTags

from autotailor.processor import rotate_image, crop_and_clean_margins, clean_background_color, clean_background_grayscale, clean_background_binary
from autotailor.ocr import configure_tesseract, detect_rotation, perform_ocr_verification

DEFAULT_CONFIG = {
    "mode": "gray",
    "ocr_language": "ukr+eng",
    "ocr_checklist": ["СХЕМАТИЧНИЙ", "ПЛАН", "Експлікація", "Креслення"],
    "rotation_keywords": ["план", "поверх", "область", "район", "громада", "вулиця", "експлікація", "будівля", "схема"],
    "report_language": "ru",
    "tessdata_dir": None
}

TRANSLATIONS = {
    "ru": {
        "title": "ОТЧЕТ О РАСПОЗНАВАНИИ (OCR REPORT)",
        "source_file": "Исходный файл",
        "mode": "Режим обработки",
        "resolution": "Размер изображения",
        "char_count": "Всего символов распознано",
        "word_count": "Всего слов распознано",
        "checklist_header": "Проверка ключевых слов по чек-листу чертежа",
        "checklist_result": "Результат сверки",
        "status_header": "Статус верификации",
        "status_passed": "УСПЕШНО ПРОЙДЕНО (PASSED)",
        "status_failed": "НЕ ПРОЙДЕНО (FAILED)",
        "ocr_text_header": "Распознанный текст",
        "found": "НАЙДЕНО",
        "not_found": "НЕ НАЙДЕНО",
        "inbox_banner": "--- Автоматический обработчик папки Inbox ---",
        "inbox_not_found": "Ошибка: Директория inbox не найдена.",
        "current_mode": "Текущий режим обработки (из config.json)",
        "no_files": "В папке Inbox нет новых изображений для обработки.",
        "found_files": "Найдено файлов для обработки",
        "processing_file": "Обработка файла",
        "auto_rot_detected": "Обнаружен интеллектуальный автоповорот: {} градусов (игнорируем EXIF {})",
        "auto_rot_failed": "Интеллектуальный автоповорот не определил ориентацию. Используется EXIF поворот: {}",
        "rotated_by": "Изображение повернуто на {} градусов.",
        "cropped_to": "Контент-зависимая обрезка краев выполнена: x={}..{}, y={}..{}",
        "cropped_fallback": "Предупреждение: Контент не обнаружен. Откат к стандартной обрезке краев.",
        "saved_png": "Сохранен PNG скан",
        "saved_pdf": "Сохранен PDF скан",
        "saved_report": "Сохранен отчет OCR",
        "done": "Обработка завершена! Результаты сохранены в папку out.",
        "file_locked_png": "Предупреждение: Файл PNG {} заблокирован. Повторная попытка с альтернативным именем...",
        "file_locked_pdf": "Предупреждение: Файл PDF {} заблокирован (возможно, открыт в просмотрщике).",
        "all_pdf_locked": "Ошибка: Не удалось сохранить PDF. Все имена файлов заблокированы.",
        "file_locked_rep": "Предупреждение: Отчет OCR {} заблокирован. Сохранение с суффиксом..."
    },
    "en": {
        "title": "OCR VERIFICATION REPORT",
        "source_file": "Source file",
        "mode": "Processing mode",
        "resolution": "Image size",
        "char_count": "Total characters recognized",
        "word_count": "Total words recognized",
        "checklist_header": "Drawing checklist keyword verification",
        "checklist_result": "Verification score",
        "status_header": "Verification status",
        "status_passed": "PASSED",
        "status_failed": "FAILED",
        "ocr_text_header": "Recognized text",
        "found": "FOUND",
        "not_found": "NOT FOUND",
        "inbox_banner": "--- AutoTailor: Inbox Processing Daemon ---",
        "inbox_not_found": "Error: Inbox directory not found.",
        "current_mode": "Current processing mode (from config.json)",
        "no_files": "No new images to process in the Inbox folder.",
        "found_files": "Found files to process",
        "processing_file": "Processing file",
        "auto_rot_detected": "Intelligent auto-rotation detected: {} degrees (overriding EXIF {})",
        "auto_rot_failed": "Intelligent auto-rotation could not identify orientation. Using EXIF rotation: {}",
        "rotated_by": "Rotated image by {} degrees.",
        "cropped_to": "Content-Bounded Auto-Cropped to coordinates: x={}..{}, y={}..{}",
        "cropped_fallback": "Warning: No content detected. Falling back to standard crop.",
        "saved_png": "Saved PNG scan",
        "saved_pdf": "Saved PDF scan",
        "saved_report": "Saved OCR report",
        "done": "Processing completed! Results saved to the out directory.",
        "file_locked_png": "Warning: PNG file {} is locked. Retrying with alternative name...",
        "file_locked_pdf": "Warning: PDF file {} is locked (probably open in a PDF viewer).",
        "all_pdf_locked": "Error: Could not save PDF scan. All filenames are locked.",
        "file_locked_rep": "Warning: OCR report {} is locked. Saving with suffix..."
    }
}

def load_config(config_path):
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                for k, v in user_config.items():
                    config[k] = v
        except Exception as e:
            print(f"Warning: Failed to parse config file: {e}. Using default settings.")
    return config

def get_exif_rotation(file_path):
    try:
        image = Image.open(file_path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            exif = dict(exif.items())
            val = exif.get(orientation)
            if val == 3:
                return 180
            elif val == 6:
                return 270
            elif val == 8:
                return 90
    except Exception:
        pass
    return 0

def process_file(file_path, output_dir, rotate_angle=0, mode='gray', config=None):
    if config is None:
        config = DEFAULT_CONFIG

    lang = config.get("report_language", "en")
    if lang not in TRANSLATIONS:
        lang = "en"
    t = TRANSLATIONS[lang]

    print(f"{t['processing_file']}: {file_path}")
    img = cv2.imread(file_path)
    if img is None:
        print("Error: Could not open or read image file.")
        return False

    # Configure Tesseract first
    configure_tesseract(config.get("tessdata_dir"))

    # Step 1: Pre-rotate image (Intelligent Auto-Rotation)
    ocr_lang = config.get("ocr_language", "ukr+eng")
    # detect_rotation uses base language for rotation (usually 'ukr')
    base_ocr_lang = ocr_lang.split('+')[0] if ocr_lang else "ukr"
    auto_rot = detect_rotation(img, config.get("rotation_keywords", []), base_ocr_lang)
    
    if auto_rot is not None:
        print(t["auto_rot_detected"].format(auto_rot, rotate_angle))
        rotate_angle = auto_rot
    else:
        print(t["auto_rot_failed"].format(rotate_angle))

    if rotate_angle != 0:
        img = rotate_image(img, rotate_angle)
        print(t["rotated_by"].format(rotate_angle))

    height, width = img.shape[:2]

    # Step 2: Content-Bounded Auto-Cropping and Margin Cleaning
    cropped = crop_and_clean_margins(img)
    # Estimate if cropping happened based on dimension mismatch
    c_height, c_width = cropped.shape[:2]
    if c_height < height or c_width < width:
        # Just print coordinates for logging (approximate)
        print(t["cropped_to"].format(0, c_width, 0, c_height))
    else:
        print(t["cropped_fallback"])

    # Step 3: Clean background
    if mode == 'color':
        final = clean_background_color(cropped)
    elif mode == 'bw':
        final = clean_background_binary(cropped)
    else:
        final = clean_background_grayscale(cropped)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_img_path = os.path.join(output_dir, f"{base_name}_scan.png")
    out_pdf_path = os.path.join(output_dir, f"{base_name}_scan.pdf")
    out_report_path = os.path.join(output_dir, f"{base_name}_scan_report.txt")

    # Save PNG scan
    try:
        cv2.imwrite(out_img_path, final)
        print(f"{t['saved_png']}: {out_img_path}")
    except PermissionError:
        print(t["file_locked_png"].format(out_img_path))
        for suffix in range(1, 100):
            alt_img_path = os.path.join(output_dir, f"{base_name}_scan_{suffix}.png")
            try:
                cv2.imwrite(alt_img_path, final)
                print(f"{t['saved_png']}: {alt_img_path}")
                out_img_path = alt_img_path
                break
            except PermissionError:
                continue

    # Save as PDF using PIL
    if len(final.shape) == 3:
        pil_img = Image.fromarray(cv2.cvtColor(final, cv2.COLOR_BGR2RGB))
    else:
        pil_img = Image.fromarray(final)

    try:
        pil_img.save(out_pdf_path, "PDF", resolution=300.0)
        print(f"{t['saved_pdf']}: {out_pdf_path}")
    except PermissionError:
        print(t["file_locked_pdf"].format(out_pdf_path))
        saved_alt = False
        for suffix in range(1, 100):
            alt_pdf_path = os.path.join(output_dir, f"{base_name}_scan_{suffix}.pdf")
            try:
                pil_img.save(alt_pdf_path, "PDF", resolution=300.0)
                print(f"{t['saved_pdf']}: {alt_pdf_path}")
                out_pdf_path = alt_pdf_path
                saved_alt = True
                break
            except PermissionError:
                continue
        if not saved_alt:
            print(t["all_pdf_locked"])

    # Step 4: Perform OCR Verification
    print("Running OCR verification...")
    ocr_text, chk_results, found_count, char_count, word_count, is_valid = perform_ocr_verification(
        final, config.get("ocr_checklist", []), ocr_lang
    )

    # Generate Report
    report_content = []
    report_content.append("==================================================")
    report_content.append(f"         {t['title']}")
    report_content.append("==================================================")
    report_content.append(f"{t['source_file']}: {os.path.basename(file_path)}")
    report_content.append(f"{t['mode']}: {mode.upper()}")
    report_content.append(f"{t['resolution']}: {width}x{height} -> {final.shape[1]}x{final.shape[0]}")
    report_content.append(f"{t['char_count']}: {char_count}")
    report_content.append(f"{t['word_count']}: {word_count}")
    report_content.append("--------------------------------------------------")
    report_content.append(f"{t['checklist_header']}:")
    
    for word, found in chk_results.items():
        status = f"[+] {t['found']}" if found else f"[-] {t['not_found']}"
        report_content.append(f"  - {word}: {status}")
        
    report_content.append("--------------------------------------------------")
    report_content.append(f"{t['checklist_result']}: {found_count} / {len(chk_results)}")
    status_text = t['status_passed'] if is_valid else t['status_failed']
    report_content.append(f"{t['status_header']}: {status_text}")
    report_content.append("==================================================")
    report_content.append(f"\n{t['ocr_text_header']}:\n")
    report_content.append(ocr_text)

    report_str = "\n".join(report_content)

    try:
        with open(out_report_path, "w", encoding="utf-8") as f_rep:
            f_rep.write(report_str)
        print(f"{t['saved_report']}: {out_report_path}")
    except PermissionError:
        print(t["file_locked_rep"].format(out_report_path))
        for suffix in range(1, 100):
            alt_report_path = os.path.join(output_dir, f"{base_name}_scan_{suffix}_report.txt")
            try:
                with open(alt_report_path, "w", encoding="utf-8") as f_rep:
                    f_rep.write(report_str)
                print(f"{t['saved_report']}: {alt_report_path}")
                break
            except PermissionError:
                continue

    # Console summary output
    print(f"\n{t['checklist_header']}:")
    for word, found in chk_results.items():
        status = f"[+] {t['found']}" if found else f"[-] {t['not_found']}"
        print(f"  - {word}: {status}")
    print(f"{t['checklist_result']}: {found_count}/{len(chk_results)}")
    print(f"{t['status_header']}: {'PASSED' if is_valid else 'FAILED'}\n")

    return out_img_path, out_pdf_path

def detect_best_profile(files, base_dir):
    """
    Scans the first available scan in the inbox to auto-detect the document language profile.
    """
    configs_dir = os.path.join(base_dir, "configs")
    if not os.path.exists(configs_dir):
        return None

    # Load all available profiles
    profiles = {}
    profile_paths = {
        "ua": os.path.join(configs_dir, "config.ua.json"),
        "ru": os.path.join(configs_dir, "config.ru.json"),
        "en": os.path.join(configs_dir, "config.en.json")
    }
    
    for name, path in profile_paths.items():
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    profiles[name] = json.load(f)
            except Exception:
                pass

    if not profiles:
        return None

    # Find the first valid image file
    sample_file = None
    for f in files:
        if os.path.basename(f).lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
            sample_file = f
            break

    if not sample_file:
        return None

    # Read and downscale sample image for fast OCR
    img = cv2.imread(sample_file)
    if img is None:
        return None

    h, w = img.shape[:2]
    scale = 800.0 / max(h, w)
    small = cv2.resize(img, (int(w * scale), int(h * scale)))
    
    if len(small.shape) == 3:
        b_ch, g_ch, r_ch = cv2.split(small)
        gray = cv2.min(cv2.min(r_ch, g_ch), b_ch)
    else:
        gray = small
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 15)
    
    pil_img = Image.fromarray(binary)
    try:
        # Check installed language packs to prevent crash
        installed_langs = pytesseract.get_languages()
        target_langs = [l for l in ["ukr", "rus", "eng"] if l in installed_langs]
        if not target_langs:
            target_langs = ["eng"]
        lang_str = "+".join(target_langs)
        text = pytesseract.image_to_string(pil_img, lang=lang_str, config='--psm 11').lower()
    except Exception:
        try:
            text = pytesseract.image_to_string(pil_img, lang="eng", config='--psm 11').lower()
        except Exception:
            return None

    # Count matching keywords
    scores = {}
    for name, p_config in profiles.items():
        score = 0
        checklist = p_config.get("ocr_checklist", [])
        rot_keywords = p_config.get("rotation_keywords", [])
        for kw in checklist + rot_keywords:
            if kw.lower() in text:
                score += 1
        scores[name] = score

    # Find highest score profile
    best_profile = max(scores, key=scores.get)
    if scores[best_profile] > 0:
        return best_profile, profiles[best_profile], scores[best_profile]
    
    return None

def process_inbox_directory(config):
    # Locate project root base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    inbox_dir = os.path.join(base_dir, "inbox")
    out_dir = os.path.join(base_dir, "out")

    # Load translations using active config
    lang = config.get("report_language", "en")
    if lang not in TRANSLATIONS:
        lang = "en"
    t = TRANSLATIONS[lang]

    print(t["inbox_banner"])
    if not os.path.exists(inbox_dir):
        print(f"{t['inbox_not_found']} ({inbox_dir})")
        return

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Get files
    extensions = ('*.jpg', '*.jpeg', '*.png', '*.tiff', '*.bmp')
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(inbox_dir, ext)))

    if not files:
        print(t["no_files"])
        return

    print(f"{t['found_files']}: {len(files)}")

    # RUN SMART PROFILE DETECTION
    print("Auto-detecting document language and config profile...")
    configure_tesseract(config.get("tessdata_dir"))
    detection_res = detect_best_profile(files, base_dir)
    if detection_res:
        profile_name, profile_config, match_count = detection_res
        print(f"[Smart Detect] Auto-configured profile: {profile_name.upper()} (keyword matches: {match_count})")
        # Apply profile configuration
        for k, v in profile_config.items():
            config[k] = v
        # Reload translations based on new profile language
        lang = config.get("report_language", "en")
        if lang not in TRANSLATIONS:
            lang = "en"
        t = TRANSLATIONS[lang]
    else:
        print("[Smart Detect] Could not confidently auto-detect language. Using default config.json settings.")

    mode = config.get("mode", "gray")
    print(f"{t['current_mode']}: {mode.upper()}")

    for f in files:
        rot = get_exif_rotation(f)
        process_file(f, out_dir, rotate_angle=rot, mode=mode, config=config)

    print(f"\n{t['done']}")

def main():
    parser = argparse.ArgumentParser(description="AutoTailor: Content-Aware Document Scanner & OCR Verifier")
    parser.add_argument("input_file", nargs="?", help="Path to input image file")
    parser.add_argument("output_dir", nargs="?", help="Path to output directory")
    parser.add_argument("rotate_angle", nargs="?", type=int, default=0, help="Fallback rotation angle (0, 90, 180, 270)")
    parser.add_argument("mode", nargs="?", default=None, choices=["color", "gray", "bw"], help="Background cleaning mode")
    parser.add_argument("--inbox", action="store_true", help="Process all images inside inbox/ directory")
    parser.add_argument("--config", default="config.json", help="Path to config.json file")

    args = parser.parse_args()

    # Locate config file relative to project root if default
    if args.config == "config.json":
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, "config.json")
    else:
        config_path = args.config

    config = load_config(config_path)

    if args.inbox:
        process_inbox_directory(config)
    else:
        if not args.input_file or not args.output_dir:
            parser.print_help()
            sys.exit(1)
            
        mode = args.mode if args.mode is not None else config.get("mode", "gray")
        process_file(args.input_file, args.output_dir, args.rotate_angle, mode, config)

if __name__ == "__main__":
    main()
