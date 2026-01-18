"""
Document Generator - Sample PDF Document Creation Utility

This module generates sample PDF documents (invoices, protocols, reports)
for testing the Smart File Organizer.
"""

import os
import random
import logging
from datetime import datetime, timedelta
from typing import List

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output directory for generated documents
OUTPUT_DIR = "./incoming_documents"

# Sample document content (Bulgarian text)
INVOICES: List[str] = [
    "Фактура за предоставените услуги по проект XYZ. Общо за плащане: 1500 лв.",
    "Фактура за консултантски услуги предоставени през месец май 2023 г. Сума: 2500 лв.",
    "Фактура за ремонтни услуги извършени на 12.06.2023 г. Общо за плащане: 450 лв.",
    "Фактура за транспортни услуги, предоставени през месец юни 2023 г. Сума: 1200 лв."
]

PROTOCOLS: List[str] = [
    "Протокол от проведеното заседание на управителния съвет на фирма ABC на 15.09.2023 г. "
    "Дискутирани теми: нови проекти, бъдещи инвестиции и пазарни стратегии.",
    "Протокол от заседание на екип за развитие на продукта, проведено на 20.11.2023 г. "
    "Решени задачи: оптимизация на текущия код и план за нови функции.",
    "Протокол от заседание на комисията за подбор на нови служители, проведено на 01.12.2023 г. "
    "Дискутирани кандидати за позицията мениджър продажби."
]

REPORTS: List[str] = [
    "Годишен отчет за финансовото състояние на фирма XYZ за 2023 г. "
    "Приходи: 1 000 000 лв., разходи: 800 000 лв.",
    "Отчет за изпълнение на проект 'Анализ на пазара' през второто тримесечие на 2024 г. "
    "Резултати: успешно завършени 3 ключови етапа.",
    "Отчет за текущото състояние на проекта за изграждане на нов офис сграда. "
    "Завършени етапи: основи, стени, покрив."
]


def generate_random_date(year: int) -> datetime:
    """
    Generate a random date within the specified year.

    Args:
        year: The year for which to generate a random date.

    Returns:
        A datetime object with a random date in the specified year.

    Raises:
        ValueError: If year is not a valid year number.
    """
    if year < 1 or year > 9999:
        raise ValueError(f"Invalid year: {year}")

    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_date = start_date + timedelta(days=random_days)
    return random_date


def create_pdf(
    doc_type: str,
    content: str,
    file_name: str,
    date: datetime
) -> str:
    """
    Create a PDF document with the specified content.

    Args:
        doc_type: Type of document (e.g., "Фактура", "Протокол", "Отчет").
        content: The main content text for the document.
        file_name: Base name for the file (without extension).
        date: Date to include in the document.

    Returns:
        The generated file name with date suffix.

    Raises:
        IOError: If the file cannot be created.
        OSError: If there are permission or disk space issues.
    """
    file_path = os.path.join(OUTPUT_DIR, f"{file_name}.pdf")

    try:
        c = canvas.Canvas(file_path, pagesize=letter)
        c.setFont("Helvetica", 12)

        # Extract month and week information
        month = date.strftime("%B")
        week_number = date.strftime("%U")

        # Add document information
        c.drawString(100, 750, f"Документ: {doc_type}")
        c.drawString(100, 730, f"Съдържание: {content[:80]}...")  # Truncate long content
        c.drawString(100, 710, f"Дата: {date.strftime('%d-%m-%Y')}")
        c.drawString(100, 690, f"Месец: {month}")
        c.drawString(100, 670, f"Седмица: {week_number}")

        c.save()
        logger.info("Created document: %s", file_path)

    except (IOError, OSError) as e:
        logger.error("Failed to create PDF %s: %s", file_path, e)
        raise

    # Generate filename with date
    file_name_with_date = f"{doc_type}_{date.strftime('%Y-%m-%d')}"
    return file_name_with_date


def setup_output_directory() -> None:
    """Create the output directory if it doesn't exist."""
    try:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            logger.info("Created output directory: %s", OUTPUT_DIR)
    except OSError as e:
        logger.error("Failed to create output directory: %s", e)
        raise


def generate_sample_documents(
    num_invoices: int = 4,
    num_protocols: int = 3,
    num_reports: int = 3,
    year: int = 2024
) -> int:
    """
    Generate a set of sample documents.

    Args:
        num_invoices: Number of invoice documents to generate.
        num_protocols: Number of protocol documents to generate.
        num_reports: Number of report documents to generate.
        year: Year for random dates.

    Returns:
        Total number of documents generated.
    """
    setup_output_directory()
    total = 0

    # Generate invoices
    for i in range(num_invoices):
        random_date = generate_random_date(year)
        file_name = create_pdf(
            "Фактура",
            random.choice(INVOICES),
            f"Фактура_{random_date.strftime('%Y-%m-%d')}_{i}",
            random_date
        )
        logger.info("Document created: %s.pdf", file_name)
        total += 1

    # Generate protocols
    for i in range(num_protocols):
        random_date = generate_random_date(year)
        file_name = create_pdf(
            "Протокол",
            random.choice(PROTOCOLS),
            f"Протокол_{random_date.strftime('%Y-%m-%d')}_{i}",
            random_date
        )
        logger.info("Document created: %s.pdf", file_name)
        total += 1

    # Generate reports
    for i in range(num_reports):
        random_date = generate_random_date(year)
        file_name = create_pdf(
            "Отчет",
            random.choice(REPORTS),
            f"Отчет_{random_date.strftime('%Y-%m-%d')}_{i}",
            random_date
        )
        logger.info("Document created: %s.pdf", file_name)
        total += 1

    return total


def main() -> None:
    """Main entry point for document generation."""
    logger.info("Starting document generation...")

    total = generate_sample_documents()

    logger.info(
        "PDF documents created in '%s'. Total: %d",
        OUTPUT_DIR, total
    )


if __name__ == "__main__":
    main()
