# Contributing to AutoTailor

First off, thank you for checking out AutoTailor! We welcome contributions of all forms, including bug reports, documentation updates, feature requests, and code modifications.

Please follow these guidelines to make the process smooth and productive for everyone.

---

## Getting Started

### Prerequisites
AutoTailor requires:
- **Python 3.8+**
- **Tesseract-OCR** (with English and Ukrainian language files installed for full OCR verification support)

### Local Environment Setup

1. **Fork and Clone the Repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/AutoTailor.git
   cd AutoTailor
   ```

2. **Set Up a Virtual Environment:**
   *On Windows:*
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
   *On macOS / Linux:*
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies in Editable/Development Mode:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Pre-Commit Hooks:**
   We use pre-commit to check code styling automatically before you commit:
   ```bash
   pre-commit install
   ```

---

## Code Style & Guidelines

To keep the codebase uniform, we enforce the following:
- **Style and Formatting:** We use **Ruff** for linting and code formatting.
- Run checks manually before pushing:
  ```bash
  ruff check .
  ruff format .
  ```
- **Type Annotations:** Encourage type hinting for arguments and return types where possible.
- **Commit Messages:** Write clear, concise imperative-style commit messages (e.g., `feat: add adaptive threshold override for dark scans`).

---

## Running Tests

All unit tests are located in the `tests/` directory.
Before submitting your pull request, run tests to ensure everything works:
```bash
python -m unittest discover -s tests
```

If you add new features, please include accompanying tests in `tests/`.

---

## Submitting Pull Requests

1. Create a descriptive branch for your changes:
   ```bash
   git checkout -b feature/your-awesome-feature
   ```
2. Commit your changes and ensure pre-commit hooks pass.
3. Push to your fork:
   ```bash
   git push origin feature/your-awesome-feature
   ```
4. Open a Pull Request (PR) against our `main` branch.
5. Provide a detailed summary of your changes in the PR description, linking any related open issues.
