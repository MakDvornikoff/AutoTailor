import cv2
import numpy as np

def rotate_image(image, angle):
    """
    Rotates an image by 90, 180, or 270 degrees.
    """
    if angle == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    elif angle == 270 or angle == -90:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image

def clean_background_color(img):
    """
    Applies channel-independent Gaussian normalization to clean backgrounds in color images.
    """
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
    """
    Normalizes background using minimum R/G/B channel mapping to preserve non-gray elements.
    """
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
    """
    Converts image to clean binary (B&W) representation using adaptive thresholding.
    """
    gray_clean = clean_background_grayscale(img)
    blurred = cv2.GaussianBlur(gray_clean, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 51, 15)
    return thresh

def crop_and_clean_margins(img):
    """
    Crops borders and cleans empty page margins automatically.
    """
    height, width = img.shape[:2]
    
    # 1. Scale down for fast analysis
    scale = 800.0 / max(height, width)
    small_w, small_h = int(width * scale), int(height * scale)
    small = cv2.resize(img, (small_w, small_h))
    
    # Convert to grayscale and get binary
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 15)
    
    # 2. Filter out border noise using connected components
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
        
        # Safety padding
        padding = 40
        crop_x1 = max(0, orig_x_min - padding)
        crop_y1 = max(0, orig_y_min - padding)
        crop_x2 = min(width, orig_x_max + padding)
        crop_y2 = min(height, orig_y_max + padding)
        
        cropped = img[crop_y1:crop_y2, crop_x1:crop_x2].copy()
        
        # Paint anything outside the content box pure white
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
        # Fallback to standard crop (2% on all sides)
        crop_x1 = int(width * 0.02)
        crop_x2 = width - crop_x1
        crop_y1 = int(height * 0.02)
        crop_y2 = height - crop_y1
        return img[crop_y1:crop_y2, crop_x1:crop_x2]
