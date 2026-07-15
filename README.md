# ✂️ AutoTailor

[Читать на русском языке](#ru-автоматический-интеллектуальный-предобработчик-сканов) | [Read in English](#en-automated-content-aware-document-scanner-preprocessor)

---

## [RU] Автоматический интеллектуальный предобработчик сканов

> **Интеллектуальный предобработчик сканов документов, выравниватель страниц (de-skewer) и OCR-верификатор.**

[![Лицензия: MIT](https://img.shields.io/badge/Лицензия-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Платформа](https://img.shields.io/badge/Платформа-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![Tesseract OCR](https://img.shields.io/badge/OCR-Tesseract-orange.svg)](https://github.com/tesseract-ocr/tesseract)

AutoTailor автоматически удаляет серый фон сканера (делая бумагу идеально белой), выравнивает перекосы и переворачивает страницы текстом вверх, обрезает лишние поля и рамки, а также распознает текст.

---

### 📊 Сравнение результатов (До / После)

| 📂 Исходный скан (До) | ✨ Очищенный результат (После) |
| :--- | :--- |
| **Проблемы:** Серый фон, тени, перекос страницы, черные поля сканера. | **Результат:** Обрезка полей, выравнивание текста, чисто белый фон. |
| <pre align="left">┌──────────────────────────────────────┐<br>│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│<br>│░░   /   \                             ░░│<br>│░░  /  _  \  _ __  _ __   __ _  _ __   ░░│<br>│░░ /  /_\  \| '__|| '_ \ / _` || '_ \  ░░│<br>│░░/  ┌───┐  \  |  | |_) | (_| || | | | ░░│<br>│░░\_/     \_/__|  | .__/ \__,_||_| |_| ░░│<br>│░░                |_|                  ░░│<br>│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│<br>│░░░░░░ [ Перекос / Серый фон / Тени ] ░░│<br>│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│<br>└──────────────────────────────────────┘</pre> | <pre align="left">┌──────────────────────────────────┐<br>│   /   \                          │<br>│  /  _  \  _ __  _ __   __ _      │<br>│ /  /_\  \| '__|| '_ \ / _` |     │<br>│/  ┌───┐  \  |  | |_) | (_| |     │<br>│\_/     \_/__|  | .__/ \__,_|     │<br>│                |_|               │<br>└──────────────────────────────────┘<br><br><b>[Распознанный текст OCR]</b><br>✓ Язык: RU<br>✓ Контрольные слова: ПЛАН, СХЕМА</pre> |
| **Фон:** `#D2D2D2` (темно-серый)<br>**Поворот:** `-12.5°` (кривой скан)<br>**Поля:** Черные рамки от сканера | **Фон:** `#FFFFFF` (идеально белый)<br>**Поворот:** `0.0°` (выровнен)<br>**Поля:** Обрезано по контурной рамке |

---

### 🚀 Умная автонастройка (Zero-Setup)

В AutoTailor встроен интеллектуальный режим автоопределения. При обработке папки с файлами программа автоматически сканирует первый лист, распознает язык документов (русский, украинский или английский) и загружает подходящие словари поиска, правила переворота страниц и язык отчетов.

> [!NOTE]
> **Не требуется ручная конфигурация** — программа подгрузит нужный профиль (`configs/config.<язык>.json`) автоматически.

---

## ⚡ Быстрый старт (Для пользователей Windows)

Вам не нужно уметь программировать или настраивать окружение. Настройка AutoTailor полностью автоматизирована.

### 1️⃣ Первоначальная настройка (Один раз)
1. Дважды кликните по файлу **`setup_windows.bat`** в папке программы.
2. Скрипт автоматически установит **Python**, систему распознавания **Tesseract-OCR** и все необходимые библиотеки.
3. Дождитесь окончания процесса. Если Windows Defender или контроль учетных записей (UAC) запросят разрешение, подтвердите его.

> [!IMPORTANT]
> Скрипт первоначальной настройки требует права администратора для автоматической установки Tesseract OCR и прописывания его в глобальные переменные окружения PATH.

### 2️⃣ Обработка документов
1. Скопируйте файлы сканов (`.jpg`, `.png`, `.bmp`) в папку **`inbox`**.
2. Дважды кликните по файлу **`Process_Inbox.bat`**.
3. Откройте папку **`out`** — там будут лежать очищенные PNG файлы, объединенные PDF-документы и текстовые отчеты с распознанным текстом.

### 3️⃣ Режимы очистки фона
Вы можете изменить алгоритм очистки, запустив один из вспомогательных файлов:
* **`Set_Mode_Gray.bat`** (По умолчанию): Очищает серый налет, но сохраняет цветные печати, подписи и синие чернила.
* **`Set_Mode_BW.bat`**: Переводит скан в черно-белый формат с высоким контрастом (идеально для текста и OCR).
* **`Set_Mode_Color.bat`**: Очищает тени, полностью сохраняя исходные цвета документа.

---

## ⚙️ Принцип работы (Конвейер)

```mermaid
graph TD
    A[Файл скана в Inbox] --> B[Автоопределение языка]
    B --> C[Выравнивание и поворот страницы через Tesseract]
    C --> D[Нормализация фона и удаление теней через OpenCV]
    D --> E[Обрезка полей и рамок через связные компоненты]
    E --> F[OCR верификация и экспорт текста]
    F --> G[Генерация PNG / PDF с поиском в Out]
```

---

## 🔧 Настройка параметров (`config.json`)

Вы можете открыть `config.json` в любом текстовом редакторе для тонкой настройки.

```json
{
  "mode": "gray",
  "ocr_language": "rus+eng",
  "ocr_checklist": ["СХЕМАТИЧЕСКИЙ", "ПЛАН", "ЭКСПЛИКАЦИЯ"],
  "rotation_keywords": ["план", "этаж", "область", "улица", "здание", "схема"],
  "report_language": "ru",
  "tessdata_dir": null
}
```

### Описание параметров

| Параметр | Тип | По умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `mode` | `string` | `"gray"` | Режим очистки фона (`gray`, `bw`, `color`). |
| `ocr_language` | `string` | `"rus+eng"` | Языковой пакет Tesseract OCR (например, `rus`, `eng`, `ukr`). |
| `ocr_checklist` | `list` | `[...]` | Ключевые слова для проверки типа документа и его валидации. |
| `rotation_keywords` | `list` | `[...]` | Ключевые слова для ориентации (поворачивает лист до горизонтального чтения слов). |
| `report_language` | `string` | `"ru"` | Язык логов консоли и текстовых отчетов (`ru` или `en`). |
| `tessdata_dir` | `string` | `null` | Пользовательский путь к языковым файлам Tesseract при необходимости. |

---

## 💻 Установка для разработчиков (Advanced)

Если вы разработчик, вы можете установить библиотеку локально через `pip` и запускать её напрямую в консоли:

```bash
# Клонирование и локальная установка
git clone https://github.com/MakDvornikoff/AutoTailor.git
cd AutoTailor
pip install .
```

### Использование через CLI

```bash
# Обработать один файл
autotailor путь/к/файлу.jpg путь/к/выходной_папке/

# Обработать все файлы в папке inbox
autotailor --inbox
```

---
---

## [EN] Automated Content-Aware Document Scanner Preprocessor

> **Automated, content-aware document scanner preprocessor, de-skewer, and OCR verifier.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform Support](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey.svg)](#)
[![Tesseract OCR](https://img.shields.io/badge/OCR-Tesseract-orange.svg)](https://github.com/tesseract-ocr/tesseract)

AutoTailor automatically removes grey scanner backgrounds (producing pure white pages), rotates/de-skews pages to be upright, crops messy borders, and extracts text for document classification.

---

### 📊 Before / After Comparison

| 📂 Raw Input Scan (Before) | ✨ Cleaned & Tailored (After) |
| :--- | :--- |
| **Issues:** Grey shadows, tilted alignment, scanner board noise. | **Results:** Cropped edges, straightened content, pure white canvas. |
| <pre align="left">┌──────────────────────────────────────┐<br>│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│<br>│░░   /   \                             ░░│<br>│░░  /  _  \  _ __  _ __   __ _  _ __   ░░│<br>│░░ /  /_\  \| '__|| '_ \ / _` || '_ \  ░░│<br>│░░/  ┌───┐  \  |  | |_) | (_| || | | | ░░│<br>│░░\_/     \_/__|  | .__/ \__,_||_| |_| ░░│<br>│░░                |_|                  ░░│<br>│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│<br>│░░░░░░ [ Tilted / Grey / Shadows ] ░░░░│<br>│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│<br>└──────────────────────────────────────┘</pre> | <pre align="left">┌──────────────────────────────────┐<br>│   /   \                          │<br>│  /  _  \  _ __  _ __   __ _      │<br>│ /  /_\  \| '__|| '_ \ / _` |     │<br>│/  ┌───┐  \  |  | |_) | (_| |     │<br>│\_/     \_/__|  | .__/ \__,_|     │<br>│                |_|               │<br>└──────────────────────────────────┘<br><br><b>[OCR Text Output]</b><br>✓ Language detected: EN<br>✓ Verified words: PLAN, DRAWING</pre> |
| **Background:** `#D2D2D2` (shadowy grey) <br>**Rotation:** `-12.5°` (skewed)<br>**Borders:** Dirty scanner margins | **Background:** `#FFFFFF` (pure white)<br>**Rotation:** `0.0°` (deskewed)<br>**Borders:** Cropped to content margin |

---

### 🚀 Smart Auto-Configuration (Zero-Setup)

AutoTailor features an intelligent language auto-detection system. When you process a batch of files, it automatically inspects the first document, detects whether your files are in English, Russian, or Ukrainian, and applies the correct language settings, rotation keywords, and verification checklists.

> [!NOTE]
> **No manual configuration required** — the program dynamically loads the correct profile (`configs/config.<lang>.json`) for you.

---

## ⚡ Quick Start (For Windows Users)

You don't need any programming experience. Setting up AutoTailor is fully automatic.

### 1️⃣ Initial Setup (Do this once)
1. Double-click the file **`setup_windows.bat`** in the program folder.
2. The setup tool will automatically install **Python**, **Tesseract-OCR**, and all required packages.
3. Wait for the process to finish. If prompted by Windows Defender or User Account Control, allow the installation.

> [!IMPORTANT]
> The setup file checks for system privileges to install Tesseract OCR and add it to the system environment variables automatically.

### 2️⃣ Processing Scans
1. Copy your scanned images (`.jpg`, `.png`, `.bmp`) into the **`inbox`** folder.
2. Double-click the file **`Process_Inbox.bat`**.
3. Open the **`out`** folder to find your cleaned PNG files, merged PDF documents, and text OCR reports.

### 3️⃣ Selecting Cleaning Modes
You can switch the cleaning engine by double-clicking the helper batch files:
* **`Set_Mode_Gray.bat`** (Default): Keeps colored stamps/signatures but makes the paper background pure white.
* **`Set_Mode_BW.bat`**: Converts scans to clean, high-contrast black & white (optimal for pure text & OCR).
* **`Set_Mode_Color.bat`**: Cleans the background shadows but preserves all original colors.

---

## ⚙️ How It Works (Pipeline)

```mermaid
graph TD
    A[Raw Scan in Inbox] --> B[Smart Language Detector]
    B --> C[Page De-skewing / Rotation via Tesseract]
    C --> D[Background Normalization & Shadow Removal]
    D --> E[Connected Component Border & Margin Cropping]
    E --> F[OCR Verification & Text Export]
    F --> G[Generate Clean PNG / Searchable PDF in Out]
```

---

## 🔧 Configuration (`config.json`)

Open `config.json` in any text editor to customize parameters.

```json
{
  "mode": "gray",
  "ocr_language": "eng",
  "ocr_checklist": ["PLAN", "DRAWING", "EXPLANATION"],
  "rotation_keywords": ["plan", "floor", "area", "building", "street"],
  "report_language": "en",
  "tessdata_dir": null
}
```

### Parameters Guide

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `mode` | `string` | `"gray"` | Background cleaning mode (`gray`, `bw`, `color`). |
| `ocr_language` | `string` | `"eng"` | Tesseract OCR language package (e.g., `eng`, `rus`, `ukr`). |
| `ocr_checklist` | `list` | `[...]` | Required keywords checked by the program to validate document type. |
| `rotation_keywords` | `list` | `[...]` | Keywords used to orient the scan (rotates sheet until keywords are horizontal). |
| `report_language` | `string` | `"en"` | Language of the generated log reports (`en` or `ru`). |
| `tessdata_dir` | `string` | `null` | Custom path to Tesseract language data files if needed. |

---

## 💻 Developer Installation (Advanced)

If you are a developer, install the package via `pip` and run it from your terminal:

```bash
# Clone and install locally
git clone https://github.com/MakDvornikoff/AutoTailor.git
cd AutoTailor
pip install .
```

### CLI Interface

```bash
# Process a single scan file
autotailor path/to/scan.jpg path/to/output/

# Process all scans in the inbox folder
autotailor --inbox
```

---

## 📄 License

This project is open-source and licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
