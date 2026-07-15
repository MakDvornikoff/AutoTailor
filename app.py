import os
import sys
import tempfile
import cv2
import numpy as np
import gradio as gr
from PIL import Image

# Ensure the local autotailor package is importable
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from autotailor.processor import rotate_image
from autotailor.ocr import configure_tesseract, detect_rotation, perform_ocr_verification

# =====================================================================
# 1. PARAMETERIZED CORE FUNCTIONS (Dynamic UI Overrides)
# =====================================================================

def clean_background_color_custom(img, low=5, high=230, blur_k=99):
    """Channel-independent Gaussian normalization with adjustable parameters."""
    height, width = img.shape[:2]
    scale = 800.0 / max(height, width)
    w_s, h_s = int(width * scale), int(height * scale)
    
    channels = cv2.split(img)
    normalized_channels = []
    
    for ch in channels:
        small_ch = cv2.resize(ch, (w_s, h_s))
        blur_small = cv2.GaussianBlur(small_ch, (blur_k, blur_k), 0)
        bg_ch = cv2.resize(blur_small, (width, height))
        
        bg_float = bg_ch.astype(np.float32)
        bg_float[bg_float == 0] = 1.0
        norm_ch = (ch.astype(np.float32) / bg_float * 255.0)
        norm_ch = np.clip(norm_ch, 0, 255).astype(np.uint8)
        normalized_channels.append(norm_ch)
        
    normalized = cv2.merge(normalized_channels)
    
    # Custom stretch
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        if i <= low:
            lut[i] = 0
        elif i >= high:
            lut[i] = 255
        else:
            lut[i] = int(((i - low) / (high - low)) * 255)
            
    return cv2.LUT(normalized, lut)

def clean_background_grayscale_custom(img, low=0, high=225, blur_k=99):
    """Grayscale background normalization with adjustable parameters."""
    b, g, r = cv2.split(img)
    gray = cv2.min(cv2.min(r, g), b)
    height, width = gray.shape
    
    scale = 800.0 / max(height, width)
    w_s, h_s = int(width * scale), int(height * scale)
    
    small_ch = cv2.resize(gray, (w_s, h_s))
    blur_small = cv2.GaussianBlur(small_ch, (blur_k, blur_k), 0)
    bg_ch = cv2.resize(blur_small, (width, height))
    
    bg_float = bg_ch.astype(np.float32)
    bg_float[bg_float == 0] = 1.0
    normalized = (gray.astype(np.float32) / bg_float * 255.0)
    normalized = np.clip(normalized, 0, 255).astype(np.uint8)
    
    # Custom stretch
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        if i <= low:
            lut[i] = 0
        elif i >= high:
            lut[i] = 255
        else:
            lut[i] = int(((i - low) / (high - low)) * 255)
            
    return cv2.LUT(normalized, lut)

def clean_background_binary_custom(img, low=0, high=225, blur_k=99, block_size=51, c_val=15):
    """Binary black and white adaptive threshold cleaning with custom parameters."""
    gray_clean = clean_background_grayscale_custom(img, low, high, blur_k)
    blurred = cv2.GaussianBlur(gray_clean, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, block_size, c_val
    )
    return thresh

def crop_and_clean_margins_custom(img, padding=40, low_perc=0.1, high_perc=99.9, border_pct=0.03):
    """Automatically crops margins based on content bounding box with adjustable percentiles."""
    height, width = img.shape[:2]
    
    # 1. Scale down for fast analysis
    scale = 800.0 / max(height, width)
    small_w, small_h = int(width * scale), int(height * scale)
    small = cv2.resize(img, (small_w, small_h))
    
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 15)
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh, connectivity=8)
    content_mask = thresh.copy()
    
    border_w = int(small_w * border_pct)
    border_h = int(small_h * border_pct)
    
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        near_border = (x < border_w) or (y < border_h) or (x + w >= small_w - border_w) or (y + h >= small_h - border_h)
        if near_border and area > 100:
            content_mask[labels == i] = 0
            
    pts = np.argwhere(content_mask > 0)
    if len(pts) > 0:
        y_coords = pts[:, 0]
        x_coords = pts[:, 1]
        
        y_min = int(np.percentile(y_coords, low_perc))
        y_max = int(np.percentile(y_coords, high_perc))
        x_min = int(np.percentile(x_coords, low_perc))
        x_max = int(np.percentile(x_coords, high_perc))
        
        orig_x_min = int(x_min / scale)
        orig_y_min = int(y_min / scale)
        orig_x_max = int(x_max / scale)
        orig_y_max = int(y_max / scale)
        
        crop_x1 = max(0, orig_x_min - padding)
        crop_y1 = max(0, orig_y_min - padding)
        crop_x2 = min(width, orig_x_max + padding)
        crop_y2 = min(height, orig_y_max + padding)
        
        cropped = img[crop_y1:crop_y2, crop_x1:crop_x2].copy()
        
        c_x1 = orig_x_min - crop_x1
        c_y1 = orig_y_min - crop_y1
        c_x2 = orig_x_max - crop_x1
        c_y2 = orig_y_max - crop_y1
        
        h_cr, w_cr = cropped.shape[:2]
        clean_mask = np.ones((h_cr, w_cr), dtype=np.uint8) * 255
        clean_mask[c_y1:c_y2, c_x1:c_x2] = 0
        
        cropped[clean_mask == 255] = [255, 255, 255]
        return cropped
    else:
        # Fallback to standard 2% crop
        crop_x1 = int(width * 0.02)
        crop_x2 = width - crop_x1
        crop_y1 = int(height * 0.02)
        crop_y2 = height - crop_y1
        return img[crop_y1:crop_y2, crop_x1:crop_x2]

# =====================================================================
# 2. GRADIO UI PROCESSOR
# =====================================================================

def process_ui(input_image, mode, rotation_mode, manual_angle, 
               low_val, high_val, blur_k, block_size, c_val,
               enable_crop, crop_padding, low_perc, high_perc,
               ocr_langs, checklist_str, rotation_str):
    if input_image is None:
        return None, None, "### ❌ Error\nPlease upload an image file first.", "", ""

    # Convert PIL to BGR OpenCV image
    img_bgr = cv2.cvtColor(np.array(input_image), cv2.COLOR_RGB2BGR)
    
    # Automatically configure local/system tesseract path
    configure_tesseract()
    
    # Process text inputs
    checklist = [w.strip() for w in checklist_str.split(",") if w.strip()]
    rotation_keywords = [w.strip() for w in rotation_str.split(",") if w.strip()]
    
    # Step 1: Handle Rotation
    applied_angle = 0
    if rotation_mode == "Auto (Keyword-based)":
        detect_lang = ocr_langs[0] if ocr_langs else "eng"
        auto_rot = detect_rotation(img_bgr, rotation_keywords, detect_lang)
        if auto_rot is not None:
            applied_angle = auto_rot
    else:
        applied_angle = int(manual_angle)
        
    if applied_angle != 0:
        img_bgr = rotate_image(img_bgr, applied_angle)
        
    # Step 2: Content-Aware Margin Cropping
    if enable_crop:
        cropped_img = crop_and_clean_margins_custom(
            img_bgr, padding=crop_padding, low_perc=low_perc, high_perc=high_perc
        )
    else:
        cropped_img = img_bgr
        
    # Step 3: Background Cleansing
    if mode == "Color":
        cleaned = clean_background_color_custom(cropped_img, low=low_val, high=high_val, blur_k=blur_k)
    elif mode == "Binary (B&W)":
        cleaned = clean_background_binary_custom(
            cropped_img, low=low_val, high=high_val, blur_k=blur_k, 
            block_size=block_size, c_val=c_val
        )
    else:  # Grayscale
        cleaned = clean_background_grayscale_custom(cropped_img, low=low_val, high=high_val, blur_k=blur_k)
        
    # Step 4: Save & Convert output files
    if len(cleaned.shape) == 3:
        cleaned_rgb = cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB)
        pil_cleaned = Image.fromarray(cleaned_rgb)
    else:
        pil_cleaned = Image.fromarray(cleaned)
        
    temp_dir = tempfile.gettempdir()
    
    # Save processed image as PNG
    out_png_path = os.path.join(temp_dir, "autotailor_scan.png")
    pil_cleaned.save(out_png_path, "PNG")
    
    # Save as PDF
    out_pdf_path = os.path.join(temp_dir, "autotailor_scan.pdf")
    pil_cleaned.save(out_pdf_path, "PDF", resolution=300.0)
    
    # Step 5: Run OCR verification
    lang_str = "+".join(ocr_langs) if ocr_langs else "eng"
    ocr_text, chk_results, found_count, char_count, word_count, is_valid = perform_ocr_verification(
        cleaned, checklist, lang_str
    )
    
    # Write OCR verification report to text file
    report_content = [
        "==================================================",
        "             OCR VERIFICATION REPORT",
        "==================================================",
        f"Processing Mode: {mode}",
        f"Auto-Cropping  : {'Enabled' if enable_crop else 'Disabled'}",
        f"Rotation Angle : {applied_angle} degrees",
        f"Character Count: {char_count}",
        f"Word Count     : {word_count}",
        "--------------------------------------------------",
        "Keyword checklist verification results:",
    ]
    for word, found in chk_results.items():
        status = "[+] FOUND" if found else "[ ] NOT FOUND"
        report_content.append(f"  - {word}: {status}")
    report_content.append("--------------------------------------------------")
    report_content.append(f"Verification Score : {found_count} / {len(checklist)}")
    report_content.append(f"Verification Status: {'PASSED' if is_valid else 'FAILED'}")
    report_content.append("==================================================\n")
    report_content.append("Raw OCR Text:\n")
    report_content.append(ocr_text)
    
    report_str = "\n".join(report_content)
    out_report_path = os.path.join(temp_dir, "autotailor_ocr_report.txt")
    with open(out_report_path, "w", encoding="utf-8") as f:
        f.write(report_str)
        
    # Format status box HTML/Markdown
    status_emoji = "🟢 PASSED" if is_valid else "🔴 FAILED"
    status_color = "#28a745" if is_valid else "#dc3545"
    status_md = f"""
<div style="padding:15px; border-radius:5px; background-color:{status_color}22; border: 1px solid {status_color}; margin-bottom:15px;">
    <h3 style="margin-top:0; color:{status_color};">{status_emoji}</h3>
    <b>Checklist Matches:</b> {found_count} / {len(checklist)}<br>
    <b>Stats:</b> {word_count} words | {char_count} characters
</div>
"""
    
    # Checklist Markdown status list
    checklist_md = "\n".join([
        f"- {'✅' if found else '❌'} **{word}**: {'Found' if found else 'Missing'}"
        for word, found in chk_results.items()
    ])
    
    return pil_cleaned, [out_png_path, out_pdf_path, out_report_path], status_md, checklist_md, ocr_text

# =====================================================================
# 3. GRADIO APP LAYOUT BUILDER
# =====================================================================

with gr.Blocks(title="AutoTailor Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 📐 AutoTailor: Smart Scan Cleansing & Document Verification
        AutoTailor automatically cleans, crops, rotates, and runs OCR verification check-lists on scanned layouts, plans, and technical documents.
        
        *Simply upload your scan, adjust parameters on the left, and view the cleaned results and OCR analytics on the right!*
        """
    )
    
    with gr.Row():
        # LEFT COLUMN - CONTROLS
        with gr.Column(scale=1):
            gr.Markdown("### 📥 Input Configuration")
            input_img = gr.Image(type="pil", label="Upload Scan (PNG, JPG, BMP)")
            
            mode = gr.Radio(
                choices=["Grayscale", "Binary (B&W)", "Color"], 
                value="Grayscale", 
                label="Scan Cleansing Mode"
            )
            
            with gr.Row():
                rot_mode = gr.Dropdown(
                    choices=["Auto (Keyword-based)", "Manual"], 
                    value="Auto (Keyword-based)", 
                    label="Rotation Detection"
                )
                manual_angle = gr.Dropdown(
                    choices=["0", "90", "180", "270"], 
                    value="0", 
                    label="Manual Rotation Angle"
                )
                
            with gr.Accordion("Advanced Contrast & Normalization", open=False):
                low_val = gr.Slider(
                    minimum=0, maximum=100, value=5, step=1, 
                    label="Contrast Stretch - Low Limit (clipping black)"
                )
                high_val = gr.Slider(
                    minimum=150, maximum=255, value=230, step=1, 
                    label="Contrast Stretch - High Limit (clipping white)"
                )
                blur_k = gr.Slider(
                    minimum=21, maximum=199, value=99, step=2, 
                    label="Gaussian Normalization Kernel (Background estimation)"
                )
                
            with gr.Accordion("B&W Adaptive Thresholding (Binary Mode Only)", open=False):
                block_size = gr.Slider(
                    minimum=3, maximum=99, value=51, step=2, 
                    label="Gaussian Adaptive Window Size"
                )
                c_val = gr.Slider(
                    minimum=0, maximum=30, value=15, step=1, 
                    label="Adaptive Subtract Constant C"
                )
                
            with gr.Accordion("Content-Aware Auto-Cropping Options", open=False):
                enable_crop = gr.Checkbox(value=True, label="Enable Auto-Cropping")
                crop_padding = gr.Slider(
                    minimum=0, maximum=100, value=40, step=1, 
                    label="Output Margin Padding (px)"
                )
                low_perc = gr.Slider(
                    minimum=0.0, maximum=5.0, value=0.1, step=0.1, 
                    label="Content Bounding Box Low Percentile Cutoff"
                )
                high_perc = gr.Slider(
                    minimum=95.0, maximum=100.0, value=99.9, step=0.1, 
                    label="Content Bounding Box High Percentile Cutoff"
                )
                
            with gr.Accordion("OCR & Smart Verification Checklist", open=False):
                ocr_langs = gr.CheckboxGroup(
                    choices=["ukr", "eng", "rus"], 
                    value=["ukr", "eng"], 
                    label="OCR Language Packs"
                )
                checklist_str = gr.Textbox(
                    value="СХЕМАТИЧНИЙ, ПЛАН, Експлікація, Креслення", 
                    label="Verification Checklist Keywords (comma separated)"
                )
                rotation_str = gr.Textbox(
                    value="план, поверх, область, район, громада, вулиця, експлікація, будівля, схема", 
                    label="Auto-Rotation Anchor Keywords"
                )
                
            submit_btn = gr.Button("⚡ Clean & Verify Scan", variant="primary")
            
        # RIGHT COLUMN - RESULTS
        with gr.Column(scale=1):
            gr.Markdown("### 📤 Output & Analysis")
            
            with gr.Tabs():
                with gr.Tab("Visual Comparison"):
                    out_img = gr.Image(type="pil", label="Processed Output Scan")
                with gr.Tab("Download Files"):
                    download_files = gr.Files(label="Processed Downloads (PNG, PDF, Text Report)")
                    
            gr.Markdown("### 📊 OCR Verification Card")
            status_box = gr.Markdown("### ⚪ Waiting for scan input...")
            
            with gr.Accordion("Checklist Breakdown", open=True):
                checklist_box = gr.Markdown("- Upload a document and click Clean to evaluate.")
                
            with gr.Accordion("Raw OCR Text Inspector", open=False):
                ocr_box = gr.Textbox(lines=10, max_lines=30, label="Extracted Plain Text")

    # Link events
    submit_btn.click(
        fn=process_ui,
        inputs=[
            input_img, mode, rot_mode, manual_angle,
            low_val, high_val, blur_k, block_size, c_val,
            enable_crop, crop_padding, low_perc, high_perc,
            ocr_langs, checklist_str, rotation_str
        ],
        outputs=[out_img, download_files, status_box, checklist_box, ocr_box]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
