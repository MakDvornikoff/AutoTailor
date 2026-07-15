import cv2
import numpy as np
import os
import sys
import pytesseract
from PIL import Image

# Configure local tesseract directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TESSDATA_DIR = os.path.join(BASE_DIR, "tessdata")
# Fallback to default if not found locally
if not os.path.exists(TESSDATA_DIR):
    TESSDATA_DIR = r"C:\AUTOMATIZATION\scantailor\tessdata"
os.environ['TESSDATA_PREFIX'] = TESSDATA_DIR

CHECKLIST = ["СХЕМАТИЧНИЙ", "ПЛАН", "Кривий", "Ріг", "Експлікація", "Дишинського"]

def rotate_image(image, angle):
    if angle == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    elif angle == 270 or angle == -90:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image

def clean_background_color(img):
    # Color mode: channel-independent Gaussian normalization
    height, width = img.shape[:2]
    scale = 800.0 / max(height, width)
    w_s, h_s = int(width * scale), int(height * scale)
    
    channels = cv2.split(img)
    normalized_channels = []
    
    for ch in channels:
        small_ch = cv2.resize(ch, (w_s, h_s))
        blur_small = cv2.GaussianBlur(small_ch, (99, 99), 0)
        bg_ch = cv2.resize(blur_small, (width, height))
        
        bg_float = bg_ch.astype(np.float32)
        bg_float[bg_float == 0] = 1.0
        norm_ch = (ch.astype(np.float32) / bg_float * 255.0)
        norm_ch = np.clip(norm_ch, 0, 255).astype(np.uint8)
        normalized_channels.append(norm_ch)
        
    normalized = cv2.merge(normalized_channels)
    
    # Soft contrast stretch for natural colors
    low = 5
    high = 230
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        if i <= low:
            lut[i] = 0
        elif i >= high:
            lut[i] = 255
        else:
            lut[i] = int(((i - low) / (high - low)) * 255)
            
    return cv2.LUT(normalized, lut)

def clean_background_grayscale(img):
    # Grayscale mode: compute pixel-wise minimum of R, G, B channels
    # to preserve all colored elements (orange building fills, blue stamps/lines) as dark gray
    b, g, r = cv2.split(img)
    gray = cv2.min(cv2.min(r, g), b)
    height, width = gray.shape
    
    scale = 800.0 / max(height, width)
    w_s, h_s = int(width * scale), int(height * scale)
    
    small_ch = cv2.resize(gray, (w_s, h_s))
    blur_small = cv2.GaussianBlur(small_ch, (99, 99), 0)
    bg_ch = cv2.resize(blur_small, (width, height))
    
    bg_float = bg_ch.astype(np.float32)
    bg_float[bg_float == 0] = 1.0
    normalized = (gray.astype(np.float32) / bg_float * 255.0)
    normalized = np.clip(normalized, 0, 255).astype(np.uint8)
    
    # Very gentle contrast stretch to keep rich grayscale gradients
    # (prevents looking like flat black and white)
    low = 0
    high = 225
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        if i <= low:
            lut[i] = 0
        elif i >= high:
            lut[i] = 255
        else:
            lut[i] = int(((i - low) / (high - low)) * 255)
            
    return cv2.LUT(normalized, lut)

def clean_background_binary(img):
    # B&W mode: grayscale clean followed by adaptive thresholding
    gray_clean = clean_background_grayscale(img)
    blurred = cv2.GaussianBlur(gray_clean, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 51, 15)
    return thresh

def perform_ocr_verification(processed_img):
    if len(processed_img.shape) == 3:
        pil_img = Image.fromarray(cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB))
    else:
        pil_img = Image.fromarray(processed_img)
        
    try:
        # Use local tessdata directory via TESSDATA_PREFIX environment variable and PSM 11
        custom_config = '--psm 11'
        text = pytesseract.image_to_string(pil_img, lang="ukr+eng", config=custom_config)
        text_lower = text.lower()
        
        chk_results = {}
        for word in CHECKLIST:
            chk_results[word] = word.lower() in text_lower
            
        found_count = sum(chk_results.values())
        char_count = len(text.strip())
        word_count = len(text.split())
        is_valid = found_count >= 1 or char_count > 100
        
        return text, chk_results, found_count, char_count, word_count, is_valid
    except Exception as e:
        return f"OCR Error: {e}", {}, 0, 0, 0, False

def detect_rotation(img):
    # Try 0, 90, 180, 270 rotations on a scaled-down binarized image
    best_angle = 0
    max_matches = -1
    best_word_count = -1
    
    h, w = img.shape[:2]
    scale = 1600.0 / max(h, w) # Resize to max 1600px for robust text size
    
    KEYWORDS_ROT = ["план", "поверх", "область", "район", "громада", "вулиця", "експлікація", "будівля", "схема"]
    
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
        b_ch, g_ch, r_ch = cv2.split(small)
        gray = cv2.min(cv2.min(r_ch, g_ch), b_ch)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 15)
        
        pil_img = Image.fromarray(binary)
        config = '--psm 11'
        try:
            text = pytesseract.image_to_string(pil_img, lang="ukr", config=config).lower()
            matches = sum(1 for kw in KEYWORDS_ROT if kw in text)
            word_count = len(text.split())
            if matches > max_matches or (matches == max_matches and word_count > best_word_count):
                max_matches = matches
                best_word_count = word_count
                best_angle = angle
        except Exception as e:
            pass
            
    if max_matches <= 0:
        return None
    return best_angle

def crop_and_clean_margins(img):
    height, width = img.shape[:2]
    
    # 1. Scale down for fast analysis
    scale = 800.0 / max(height, width)
    small_w, small_h = int(width * scale), int(height * scale)
    small = cv2.resize(img, (small_w, small_h))
    
    # Convert to grayscale and get binary
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 15)
    
    # 2. Filter out border noise using connected components
    # Any component overlapping with the outer 3% border zone with area > 100 is filtered out (desk background).
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh, connectivity=8)
    content_mask = thresh.copy()
    
    border_w = int(small_w * 0.03)
    border_h = int(small_h * 0.03)
    
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        near_border = (x < border_w) or (y < border_h) or (x + w >= small_w - border_w) or (y + h >= small_h - border_h)
        if near_border and area > 100:
            content_mask[labels == i] = 0
            
    pts = np.argwhere(content_mask > 0)
    if len(pts) > 0:
        # Use percentiles to filter out tiny dust noise outliers
        y_coords = pts[:, 0]
        x_coords = pts[:, 1]
        
        y_min = int(np.percentile(y_coords, 0.1))
        y_max = int(np.percentile(y_coords, 99.9))
        x_min = int(np.percentile(x_coords, 0.1))
        x_max = int(np.percentile(x_coords, 99.9))
        
        # Scale back to original resolution
        orig_x_min = int(x_min / scale)
        orig_y_min = int(y_min / scale)
        orig_x_max = int(x_max / scale)
        orig_y_max = int(y_max / scale)
        
        # Safety padding of 40 pixels
        padding = 40
        crop_x1 = max(0, orig_x_min - padding)
        crop_y1 = max(0, orig_y_min - padding)
        crop_x2 = min(width, orig_x_max + padding)
        crop_y2 = min(height, orig_y_max + padding)
        
        cropped = img[crop_y1:crop_y2, crop_x1:crop_x2].copy()
        
        # Paint anything outside the content box pure white (255, 255, 255)
        c_x1 = orig_x_min - crop_x1
        c_y1 = orig_y_min - crop_y1
        c_x2 = orig_x_max - crop_x1
        c_y2 = orig_y_max - crop_y1
        
        h_cr, w_cr = cropped.shape[:2]
        clean_mask = np.ones((h_cr, w_cr), dtype=np.uint8) * 255
        clean_mask[c_y1:c_y2, c_x1:c_x2] = 0
        
        cropped[clean_mask == 255] = [255, 255, 255]
        print(f"Content-Bounded Auto-Cropped to coordinates: x={crop_x1}..{crop_x2}, y={crop_y1}..{crop_y2}")
        return cropped
    else:
        # Fallback to standard crop (2% on all sides) if no content detected
        print("Warning: No content detected. Falling back to standard crop.")
        crop_x1 = int(width * 0.02)
        crop_x2 = width - crop_x1
        crop_y1 = int(height * 0.02)
        crop_y2 = height - crop_y1
        return img[crop_y1:crop_y2, crop_x1:crop_x2]

def process_file(file_path, output_dir, rotate_angle=0, mode='gray'):
    print(f"Processing file: {file_path}")
    img = cv2.imread(file_path)
    if img is None:
        print("Error: Could not open or read image file.")
        return False
        
    # Step 1: Pre-rotate image
    auto_rot = detect_rotation(img)
    if auto_rot is not None:
        print(f"Intelligent auto-rotation detected: {auto_rot} degrees (overriding EXIF {rotate_angle})")
        rotate_angle = auto_rot
    else:
        print(f"Intelligent auto-rotation could not identify orientation. Using EXIF rotation: {rotate_angle}")
        
    if rotate_angle != 0:
        img = rotate_image(img, rotate_angle)
        print(f"Rotated image by {rotate_angle} degrees.")
        
    height, width = img.shape[:2]
        
    # Step 2: Content-Bounded Auto-Cropping and Margin Cleaning
    cropped = crop_and_clean_margins(img)
    
    # Step 3: Clean background
    if mode == 'color':
        final = clean_background_color(cropped)
    elif mode == 'bw':
        final = clean_background_binary(cropped)
    else:
        # Default is grayscale (gray)
        final = clean_background_grayscale(cropped)
        
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_img_path = os.path.join(output_dir, f"{base_name}_scan.png")
    out_pdf_path = os.path.join(output_dir, f"{base_name}_scan.pdf")
    out_report_path = os.path.join(output_dir, f"{base_name}_scan_report.txt")
    
    # Save Image
    try:
        cv2.imwrite(out_img_path, final)
        print(f"Saved PNG scan: {out_img_path}")
    except PermissionError:
        print(f"Warning: Image file {out_img_path} is locked. Retrying with alternative name...")
        for suffix in range(1, 100):
            alt_img_path = os.path.join(output_dir, f"{base_name}_scan_{suffix}.png")
            try:
                cv2.imwrite(alt_img_path, final)
                print(f"Saved PNG to alternative filename: {alt_img_path}")
                out_img_path = alt_img_path
                break
            except PermissionError:
                continue
                
    # Save as PDF using PIL with locked file handling
    if len(final.shape) == 3:
        pil_img = Image.fromarray(cv2.cvtColor(final, cv2.COLOR_BGR2RGB))
    else:
        pil_img = Image.fromarray(final)
        
    try:
        pil_img.save(out_pdf_path, "PDF", resolution=300.0)
        print(f"Saved PDF scan: {out_pdf_path}")
    except PermissionError:
        print(f"Warning: PDF file {out_pdf_path} is locked (probably open in a PDF reader).")
        saved_alt = False
        for suffix in range(1, 100):
            alt_pdf_path = os.path.join(output_dir, f"{base_name}_scan_{suffix}.pdf")
            try:
                pil_img.save(alt_pdf_path, "PDF", resolution=300.0)
                print(f"Saved PDF to alternative filename: {alt_pdf_path}")
                out_pdf_path = alt_pdf_path
                saved_alt = True
                break
            except PermissionError:
                continue
        if not saved_alt:
            print("Error: Could not save PDF scan. All filenames are locked. Please close your PDF reader.")
            
    # Step 4: Perform OCR Verification
    print("Running OCR verification...")
    ocr_text, chk_results, found_count, char_count, word_count, is_valid = perform_ocr_verification(final)
    
    # Generate report
    report_content = []
    report_content.append("==================================================")
    report_content.append("         ОТЧЕТ О РАСПОЗНАВАНИИ (OCR REPORT)")
    report_content.append("==================================================")
    report_content.append(f"Исходный файл: {os.path.basename(file_path)}")
    report_content.append(f"Режим обработки: {mode.upper()}")
    report_content.append(f"Размер изображения: {width}x{height} -> {final.shape[1]}x{final.shape[0]}")
    report_content.append(f"Всего символов распознано: {char_count}")
    report_content.append(f"Всего слов распознано: {word_count}")
    report_content.append("--------------------------------------------------")
    report_content.append("Проверка ключевых слов по чек-листу чертежа:")
    for word, found in chk_results.items():
        status = "[+] НАЙДЕНО" if found else "[-] НЕ НАЙДЕНО"
        report_content.append(f"  - {word}: {status}")
    report_content.append("--------------------------------------------------")
    report_content.append(f"Результат сверки: {found_count} из {len(CHECKLIST)} найдено")
    report_content.append(f"Статус верификации: {'УСПЕШНО ПРОЙДЕНО (PASSED)' if is_valid else 'НЕ ПРОЙДЕНО (FAILED)'}")
    report_content.append("==================================================")
    report_content.append("\nРаспознанный текст:\n")
    report_content.append(ocr_text)
    
    report_str = "\n".join(report_content)
    
    try:
        with open(out_report_path, "w", encoding="utf-8") as f_rep:
            f_rep.write(report_str)
        print(f"Saved OCR report: {out_report_path}")
    except PermissionError:
        print(f"Warning: OCR report {out_report_path} is locked. Saving with suffix...")
        for suffix in range(1, 100):
            alt_report_path = os.path.join(output_dir, f"{base_name}_scan_{suffix}_report.txt")
            try:
                with open(alt_report_path, "w", encoding="utf-8") as f_rep:
                    f_rep.write(report_str)
                print(f"Saved report to: {alt_report_path}")
                break
            except PermissionError:
                continue
                
    # Print status to console (safe from CP1251 errors)
    print("\nChecklist Verification:")
    for word, found in chk_results.items():
        status = "[+] FOUND" if found else "[-] NOT FOUND"
        print(f"  - {word}: {status}")
    print(f"Verification Score: {found_count}/{len(CHECKLIST)}")
    print(f"Verification Status: {'PASSED' if is_valid else 'FAILED'}\n")
    
    return out_img_path, out_pdf_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_scan.py <input_file> <output_dir> [rotate_angle] [mode: color|gray|bw]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    rotate_angle = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    mode = sys.argv[4] if len(sys.argv) > 4 else 'gray'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    process_file(input_file, output_dir, rotate_angle, mode)
