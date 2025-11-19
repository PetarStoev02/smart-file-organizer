# SmartFileSorter

SmartFileSorter is an automated PDF intake pipeline that watches a drop folder, performs zero-shot classification on each document, and files it away inside a structured archive organized by document type, year, month, and week. The repo also ships with a lightweight PDF generator so you can produce realistic sample data for demos or tests.

## Contents

| File | Description |
| --- | --- |
| `sorter.py` | Long-running watcher that classifies PDFs using a Hugging Face zero-shot classifier and moves them into the correct archive folder. |
| `documents.py` | Utility that fabricates Bulgarian-language invoices, protocols, and reports as PDFs using ReportLab. Helpful when you need seed data. |

When started, `sorter.py` creates the expected folder tree under `./sorted_documents` (2020‑2030, months, weeks) and keeps polling `./incoming_documents` every 30 seconds.

## Prerequisites

- Python 3.10+ (tested on Linux)
- pip with internet access (for downloading the Transformers model on first run)
- System packages required by `torch`/`transformers` (see their docs if installation fails)

### Python dependencies

Install the runtime dependencies into your virtual environment of choice:

```bash
pip install transformers torch pdfplumber reportlab
```

`transformers` automatically downloads the default zero-shot model (`facebook/bart-large-mnli`) the first time you invoke the pipeline.

## Quick Start

1. **Clone & install dependencies**
   ```bash
   git clone <repo-url>
   cd SmartFileSorter
   pip install transformers torch pdfplumber reportlab
   ```
2. **Generate sample PDFs (optional but recommended)**
   ```bash
   python documents.py
   ```
   This creates Bulgarian-language sample invoices, protocols, and reports inside `./incoming_documents`.
3. **Start the sorter**
   ```bash
   python sorter.py
   ```
   Keep the process running; it polls every 30 s, classifies each PDF, and moves it into `./sorted_documents/<Type>/<Year>/Month_<n>/Week_<n>/`.

## How It Works

1. **Watching for new files** – `sorter.py` ensures the `incoming_documents` and `sorted_documents` folders exist, then loops indefinitely checking for new PDFs.
2. **PDF text extraction** – Each PDF is parsed with `pdfplumber` to gather text content. Empty files are skipped with a warning.
3. **Zero-shot classification** – The extracted text is sent to the Hugging Face pipeline with candidate labels `Invoice`, `Protocol`, and `Report`. The best label becomes the archive destination.
4. **Hierarchical filing** – Files are moved with `shutil` into a tree of document type → year (2020‑2030) → month (`Month_<n>`) → week (`Week_<n>`). Duplicate filenames are preserved by suffixing `_1`, `_2`, etc.
5. **Progress feedback** – The console shows classification results plus a countdown until the next polling cycle so you can monitor activity at a glance.

## Configuration

Tune behavior by editing the constants near the top of `sorter.py`:

- `INPUT_DIR` / `OUTPUT_DIR` – change watcher and archive roots.
- `CHECK_INTERVAL` – seconds between folder scans (default 30).
- `DOCUMENT_TREE` – names of the top-level archive folders to pre-create. Update this if you add new labels.

If you extend the candidate labels in `classify_document`, make sure they stay in sync with `DOCUMENT_TREE`.

## Directory Layout

```
incoming_documents/     # Drop PDFs here (created automatically)
sorted_documents/
├── Invoices/
│   └── 2024/Month_12/Week_1/<file>.pdf
├── Protocols/
└── Reports/
```

The watcher creates the full 2020‑2030 range so you can move historical files without additional setup.

## Sample Output

```
Document Отчет_2024-11-07.pdf classified as: Report
Sorting document: Отчет_2024-11-07.pdf | Classified as: Report | Remaining time: 28s
File ./incoming_documents/Отчет_2024-11-07.pdf moved to ./sorted_documents/Report/2024/Month_11/Week_2/Отчет_2024-11-07.pdf
```

## Troubleshooting

- **Model download fails** – ensure the machine has internet access; optionally pre-download the model using `transformers-cli`.
- **Torch wheel errors** – install a torch version that matches your Python and CUDA/CPU setup (see pytorch.org for the correct command).
- **Corrupt PDFs** – invalid or image-only PDFs produce empty text and are skipped. Convert them to searchable PDFs before rerunning.

## License

MIT © SmartFileSorter contributors
