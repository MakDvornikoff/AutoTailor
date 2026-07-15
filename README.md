# AutoTailor

AutoTailor is an automatic program for cleaning, rotating, and cropping scanned drawings, plans, and documents.

It automatically removes grey scan backgrounds (making pages pure white), rotates pages to be right-side up, crops borders, and extracts text.

---

## Quick Start (For Windows Users)

You do not need to know how to program or install software manually. Setting up AutoTailor is fully automatic.

### 1. Initial Setup (Do this once)
1. Double-click the file **`setup_windows.bat`** in the program folder.
2. The setup tool will automatically install **Python**, **Tesseract-OCR**, and all required packages.
3. Wait for it to finish. If prompted by Windows, allow the installation.

### 2. Processing Scans
1. Copy your scanned images (JPG, PNG, BMP) into the **`inbox`** folder.
2. Double-click the file **`Process_Inbox.bat`**.
3. The program will automatically clean, crop, rotate, and extract text from your files.
4. Open the **`out`** folder to find your cleaned PNG files, PDF documents, and text OCR reports.

### 3. Switching Cleaning Modes
You can switch how the program cleans the scans by double-clicking the following helper files:
* **`Set_Mode_Gray.bat`** (Default): Keeps colored stamps/signatures but makes the paper background white.
* **`Set_Mode_BW.bat`**: Converts scans to clean, high-contrast black & white (great for pure text).
* **`Set_Mode_Color.bat`**: Cleans the background but preserves full colors.

---

## Configuration (`config.json`)

You can open the `config.json` file in a text editor to customize settings. 

Example configuration with generic settings:
```json
{
  "mode": "gray",
  "ocr_language": "eng",
  "ocr_checklist": [
    "PLAN",
    "DRAWING",
    "EXPLANATION"
  ],
  "rotation_keywords": [
    "plan",
    "floor",
    "area",
    "building",
    "street"
  ],
  "report_language": "en",
  "tessdata_dir": null
}
```

* `ocr_checklist`: Words that the program checks for to confirm if the document is valid.
* `rotation_keywords`: Key words used by the program to determine which way to rotate the page (e.g. looking for words like "plan" or "street" to align the text).
* `report_language`: Language of the generated text reports (`en` for English, `ru` for Russian).

---

## Developer Installation (Advanced)

If you are a developer, install it via pip:

```bash
pip install .
```

Run via CLI:
```bash
# Process single file
autotailor path/to/scan.jpg path/to/output/

# Process folder
autotailor --inbox
```

---

## License

This project is licensed under the MIT License.
