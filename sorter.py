"""
Smart File Organizer - PDF Document Classification and Sorting Service

This module provides functionality to automatically classify PDF documents
using zero-shot classification and organize them into a structured directory tree.
"""

import os
import shutil
import time
import logging
from datetime import datetime
from typing import Optional

import pdfplumber
from transformers import pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sorter.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Parameters for the directories
INPUT_DIR = os.environ.get("SORTER_INPUT_DIR", "./incoming_documents")
OUTPUT_DIR = os.environ.get("SORTER_OUTPUT_DIR", "./sorted_documents")
CHECK_INTERVAL = int(os.environ.get("SORTER_CHECK_INTERVAL", "30"))

# Document types for classification
DOCUMENT_TYPES = ["Invoices", "Protocols", "Reports"]
CANDIDATE_LABELS = ["Invoice", "Protocol", "Report"]

# Mapping from classification labels to directory names
LABEL_TO_DIR = {
    "Invoice": "Invoices",
    "Protocol": "Protocols",
    "Report": "Reports"
}


def setup_directory_structure() -> None:
    """Create the directory structure for sorted documents."""
    for doc_type in DOCUMENT_TYPES:
        for year in range(2020, 2031):
            for month in range(1, 13):
                for week in range(1, 6):
                    path = os.path.join(
                        OUTPUT_DIR, doc_type, str(year),
                        f"Month_{month}", f"Week_{week}"
                    )
                    os.makedirs(path, exist_ok=True)

    os.makedirs(INPUT_DIR, exist_ok=True)
    logger.info("Directory structure initialized")


def load_classifier():
    """Load the zero-shot classification pipeline."""
    try:
        logger.info("Loading classification model...")
        clf = pipeline("zero-shot-classification")
        logger.info("Classification model loaded successfully")
        return clf
    except Exception as e:
        logger.error("Failed to load classification model: %s", e)
        raise


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text content from a PDF document.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text as a string, or empty string if extraction fails.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text.strip()
    except FileNotFoundError:
        logger.error("File not found: %s", file_path)
        return ""
    except Exception as e:
        logger.error("Error extracting text from %s: %s", file_path, e)
        return ""


def classify_document(file_path: str, classifier) -> Optional[str]:
    """
    Classify a document using zero-shot classification.

    Args:
        file_path: Path to the PDF file.
        classifier: The classification pipeline.

    Returns:
        The document type label, or None if classification fails.
    """
    text = extract_text_from_pdf(file_path)

    if not text:
        logger.warning("No text extracted from %s. Skipping classification.", file_path)
        return None

    try:
        result = classifier(text, CANDIDATE_LABELS)
        doc_type = result['labels'][0]
        confidence = result['scores'][0]
        logger.debug(
            "Classified %s as %s with confidence %.2f",
            file_path, doc_type, confidence
        )
        return doc_type
    except Exception as e:
        logger.error("Classification failed for %s: %s", file_path, e)
        return None


def get_week_of_month(date: datetime) -> int:
    """
    Calculate the week number within a month (1-5).

    Args:
        date: The datetime object.

    Returns:
        Week number (1-5).
    """
    day_of_month = date.day
    week_of_month = (day_of_month - 1) // 7 + 1
    return min(week_of_month, 5)  # Cap at 5 weeks


def move_file_to_correct_directory(
    file_path: str,
    doc_type: str,
    document_date: datetime
) -> Optional[str]:
    """
    Move a file to the appropriate directory based on classification.

    Args:
        file_path: Source file path.
        doc_type: Document type classification label.
        document_date: Date to use for organizing.

    Returns:
        The target file path if successful, None otherwise.
    """
    if doc_type is None:
        return None

    # Map classification label to directory name
    dir_name = LABEL_TO_DIR.get(doc_type, doc_type + "s")

    week_of_month = get_week_of_month(document_date)

    target_dir = os.path.join(
        OUTPUT_DIR, dir_name, str(document_date.year),
        f"Month_{document_date.month}", f"Week_{week_of_month}"
    )

    try:
        os.makedirs(target_dir, exist_ok=True)
    except OSError as e:
        logger.error("Failed to create directory %s: %s", target_dir, e)
        return None

    target_file_path = os.path.join(target_dir, os.path.basename(file_path))

    # Handle duplicate files
    if os.path.exists(target_file_path):
        logger.info("Found duplicate file: %s. Renaming.", target_file_path)
        base_name, ext = os.path.splitext(target_file_path)
        counter = 1
        while os.path.exists(f"{base_name}_{counter}{ext}"):
            counter += 1
        target_file_path = f"{base_name}_{counter}{ext}"

    try:
        shutil.move(file_path, target_file_path)
        logger.info("Moved %s to %s", file_path, target_file_path)
        return target_file_path
    except (OSError, shutil.Error) as e:
        logger.error("Failed to move file %s: %s", file_path, e)
        return None


def display_sorting_progress(
    file_name: str,
    doc_type: str,
    remaining_time: int
) -> None:
    """
    Display sorting progress in the console.

    Args:
        file_name: Name of the file being processed.
        doc_type: Document type classification.
        remaining_time: Seconds remaining until next check.
    """
    print(
        f"\rSorting document: {file_name} | Classified as: {doc_type} | "
        f"Remaining time: {remaining_time}s",
        end=""
    )


def process_files(classifier) -> int:
    """
    Process all files in the input directory.

    Args:
        classifier: The classification pipeline.

    Returns:
        Number of files successfully processed.
    """
    try:
        files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.pdf')]
    except OSError as e:
        logger.error("Failed to list input directory: %s", e)
        return 0

    if not files:
        logger.info("No PDF files to sort. Checking again in %d seconds.", CHECK_INTERVAL)
        return 0

    processed = 0
    for file_name in files:
        file_path = os.path.join(INPUT_DIR, file_name)

        doc_type = classify_document(file_path, classifier)

        if doc_type is None:
            continue

        logger.info("Document %s classified as: %s", file_name, doc_type)

        display_sorting_progress(file_name, doc_type, CHECK_INTERVAL)

        result = move_file_to_correct_directory(file_path, doc_type, datetime.now())
        if result:
            processed += 1

    return processed


def main() -> None:
    """Main entry point for the document sorter service."""
    logger.info("Starting Smart File Organizer...")

    setup_directory_structure()
    classifier = load_classifier()

    logger.info("Monitoring %s for incoming documents...", INPUT_DIR)

    while True:
        start_time = time.time()

        processed = process_files(classifier)

        elapsed_time = time.time() - start_time
        if processed > 0:
            logger.info(
                "Processed %d files in %.2f seconds.",
                processed, elapsed_time
            )

        for remaining_time in range(CHECK_INTERVAL, 0, -1):
            display_sorting_progress("Waiting...", "", remaining_time)
            time.sleep(1)
        print()  # New line after countdown


if __name__ == "__main__":
    main()
