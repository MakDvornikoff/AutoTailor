# AutoTailor

AutoTailor is an automated, content-aware document scanner preprocessor and OCR verifier. It is designed to clean, rotate, crop, and verify scanned technical drawings, plans, and general documents.

---

## Features

* **Intelligent Auto-Rotation (Skew Correction):** Detects and corrects image orientation (0, 90, 180, 270 degrees) using Tesseract OCR keyword analysis.
* **Content-Bounded Auto-Cropping:** Identifies actual page boundaries using connected component analysis, filters out desk margins/border noise, and pads/flattens the margins to pure white.
* **Adaptive Background Cleaning (3 Modes):**
  * `gray` (Grayscale - default): Normalizes the background using Gaussian normalization and minimum channel mapping to preserve all non-gray details (stamps, signatures) as dark gray while keeping page clean.
  * `bw` (Black & White): Binarizes the scan with adaptive thresholding for high-contrast text.
  * `color` (Clean Color): Normalizes brightness and shadows across color channels for crisp, color-accurate scans.
* **Bilingual Reporting & Interface:** Fully localized logs and generated reports in English and Russian, configurable on the fly.
* **JSON Configuration:** Easily customize checklists, rotation keywords, default cleaning modes, and directory paths.

---

## Installation

### 1. Install Tesseract OCR

AutoTailor requires Tesseract OCR installed on your system. 

* **Windows:**
  Download and run the installer from [UB-Mannheim Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).
  *(Make sure to download language packs like Ukrainian and Russian during installation if needed)*.
* **macOS:**
  ```bash
  brew install tesseract tesseract-lang
  ```
* **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt update
  sudo apt install tesseract-ocr tesseract-ocr-ukr tesseract-ocr-rus
  ```

### 2. Install AutoTailor

Clone this repository and install using `pip`:

```bash
git clone https://github.com/yourusername/AutoTailor.git
cd AutoTailor
pip install .
```

---

## Configuration (`config.json`)

The project uses a `config.json` file in the root directory. You can edit this file to customize behavior:

```json
{
  "mode": "gray",
  "ocr_language": "ukr+eng",
  "ocr_checklist": [
    "СХЕМАТИЧНИЙ",
    "ПЛАН",
    "Кривий",
    "Ріг"
  ],
  "rotation_keywords": [
    "план",
    "поверх",
    "область",
    "експлікація"
  ],
  "report_language": "en",
  "tessdata_dir": null
}
```

### Config Options:
* `mode`: Default image processing mode (`gray`, `bw`, or `color`).
* `ocr_language`: Tesseract languages to use (e.g. `ukr+eng` or `eng+rus`).
* `ocr_checklist`: Words that the document must contain to pass OCR verification.
* `rotation_keywords`: Words used by the intelligent auto-rotation algorithm to determine the correct page orientation.
* `report_language`: The language of stdout console logs and generated OCR text reports (`en` for English, `ru` for Russian).
* `tessdata_dir`: Absolute path to Tesseract `tessdata/` folder. If `null`, AutoTailor will auto-detect local and system installations.

---

## Usage

### Command Line Interface

If installed via pip, run the CLI utility directly:

```bash
# Process a single file
autotailor path/to/input.jpg path/to/output_dir/ 0 gray

# Process all files in the inbox folder
autotailor --inbox
```

Alternatively, you can run it as a python module from the project root:

```bash
# Process all files in inbox/ folder
python -m autotailor.cli --inbox
```

### Batch Scripts (Windows)
Double-click the batch files at the root of the project to change modes or run processing:
* `Process_Inbox.bat`: Run the batch processor daemon on the `inbox/` folder.
* `Set_Mode_Gray.bat`: Set background cleaning to grayscale.
* `Set_Mode_BW.bat`: Set background cleaning to high-contrast black & white.
* `Set_Mode_Color.bat`: Set background cleaning to clean color.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
