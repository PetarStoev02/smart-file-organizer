"""Tests for the sorter module."""

import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest

# Mock transformers before importing sorter
import sys
sys.modules['transformers'] = MagicMock()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sorter import (
    extract_text_from_pdf,
    classify_document,
    get_week_of_month,
    move_file_to_correct_directory,
    display_sorting_progress,
    LABEL_TO_DIR,
    CANDIDATE_LABELS,
)


class TestGetWeekOfMonth:
    """Tests for get_week_of_month function."""

    def test_first_week(self):
        """Day 1-7 should be week 1."""
        assert get_week_of_month(datetime(2024, 1, 1)) == 1
        assert get_week_of_month(datetime(2024, 1, 7)) == 1

    def test_second_week(self):
        """Day 8-14 should be week 2."""
        assert get_week_of_month(datetime(2024, 1, 8)) == 2
        assert get_week_of_month(datetime(2024, 1, 14)) == 2

    def test_third_week(self):
        """Day 15-21 should be week 3."""
        assert get_week_of_month(datetime(2024, 1, 15)) == 3
        assert get_week_of_month(datetime(2024, 1, 21)) == 3

    def test_fourth_week(self):
        """Day 22-28 should be week 4."""
        assert get_week_of_month(datetime(2024, 1, 22)) == 4
        assert get_week_of_month(datetime(2024, 1, 28)) == 4

    def test_fifth_week(self):
        """Day 29-31 should be week 5."""
        assert get_week_of_month(datetime(2024, 1, 29)) == 5
        assert get_week_of_month(datetime(2024, 1, 31)) == 5

    def test_caps_at_week_5(self):
        """Week should never exceed 5."""
        # Day 31 would mathematically be week 5
        assert get_week_of_month(datetime(2024, 1, 31)) <= 5


class TestExtractTextFromPdf:
    """Tests for extract_text_from_pdf function."""

    def test_file_not_found(self):
        """Should return empty string for non-existent file."""
        result = extract_text_from_pdf("/nonexistent/path/file.pdf")
        assert result == ""

    @patch('sorter.pdfplumber.open')
    def test_successful_extraction(self, mock_pdfplumber):
        """Should extract text from PDF pages."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test content"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.return_value = mock_pdf

        result = extract_text_from_pdf("test.pdf")
        assert result == "Test content"

    @patch('sorter.pdfplumber.open')
    def test_multiple_pages(self, mock_pdfplumber):
        """Should concatenate text from multiple pages."""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.return_value = mock_pdf

        result = extract_text_from_pdf("test.pdf")
        assert result == "Page 1Page 2"

    @patch('sorter.pdfplumber.open')
    def test_empty_page(self, mock_pdfplumber):
        """Should handle pages with no text."""
        mock_page = Mock()
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.return_value = mock_pdf

        result = extract_text_from_pdf("test.pdf")
        assert result == ""

    @patch('sorter.pdfplumber.open')
    def test_exception_handling(self, mock_pdfplumber):
        """Should return empty string on exception."""
        mock_pdfplumber.side_effect = Exception("PDF error")

        result = extract_text_from_pdf("test.pdf")
        assert result == ""


class TestClassifyDocument:
    """Tests for classify_document function."""

    @patch('sorter.extract_text_from_pdf')
    def test_no_text_returns_none(self, mock_extract):
        """Should return None when no text is extracted."""
        mock_extract.return_value = ""
        mock_classifier = Mock()

        result = classify_document("test.pdf", mock_classifier)
        assert result is None

    @patch('sorter.extract_text_from_pdf')
    def test_successful_classification(self, mock_extract):
        """Should return classified label."""
        mock_extract.return_value = "This is an invoice document"
        mock_classifier = Mock()
        mock_classifier.return_value = {
            'labels': ['Invoice', 'Protocol', 'Report'],
            'scores': [0.9, 0.05, 0.05]
        }

        result = classify_document("test.pdf", mock_classifier)
        assert result == "Invoice"

    @patch('sorter.extract_text_from_pdf')
    def test_classifier_exception(self, mock_extract):
        """Should return None on classifier exception."""
        mock_extract.return_value = "Some text"
        mock_classifier = Mock()
        mock_classifier.side_effect = Exception("Model error")

        result = classify_document("test.pdf", mock_classifier)
        assert result is None


class TestMoveFileToCorrectDirectory:
    """Tests for move_file_to_correct_directory function."""

    def test_none_doc_type_returns_none(self):
        """Should return None when doc_type is None."""
        result = move_file_to_correct_directory(
            "test.pdf", None, datetime.now()
        )
        assert result is None

    def test_successful_move(self):
        """Should move file to correct directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source file
            source_file = os.path.join(tmpdir, "test.pdf")
            with open(source_file, 'w') as f:
                f.write("test")

            # Patch OUTPUT_DIR
            with patch('sorter.OUTPUT_DIR', tmpdir):
                test_date = datetime(2024, 6, 15)  # Week 3
                result = move_file_to_correct_directory(
                    source_file, "Invoice", test_date
                )

                assert result is not None
                assert os.path.exists(result)
                assert "Invoices" in result
                assert "2024" in result
                assert "Month_6" in result
                assert "Week_3" in result

    def test_duplicate_file_handling(self):
        """Should rename duplicate files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create target directory and existing file
            target_dir = os.path.join(
                tmpdir, "Invoices", "2024", "Month_1", "Week_1"
            )
            os.makedirs(target_dir)
            existing_file = os.path.join(target_dir, "test.pdf")
            with open(existing_file, 'w') as f:
                f.write("existing")

            # Create source file
            source_file = os.path.join(tmpdir, "test.pdf")
            with open(source_file, 'w') as f:
                f.write("new")

            with patch('sorter.OUTPUT_DIR', tmpdir):
                test_date = datetime(2024, 1, 1)
                result = move_file_to_correct_directory(
                    source_file, "Invoice", test_date
                )

                assert result is not None
                assert "_1.pdf" in result


class TestLabelToDir:
    """Tests for label to directory mapping."""

    def test_invoice_mapping(self):
        """Invoice should map to Invoices."""
        assert LABEL_TO_DIR["Invoice"] == "Invoices"

    def test_protocol_mapping(self):
        """Protocol should map to Protocols."""
        assert LABEL_TO_DIR["Protocol"] == "Protocols"

    def test_report_mapping(self):
        """Report should map to Reports."""
        assert LABEL_TO_DIR["Report"] == "Reports"


class TestCandidateLabels:
    """Tests for candidate labels configuration."""

    def test_all_labels_present(self):
        """Should have all three labels."""
        assert "Invoice" in CANDIDATE_LABELS
        assert "Protocol" in CANDIDATE_LABELS
        assert "Report" in CANDIDATE_LABELS

    def test_label_count(self):
        """Should have exactly 3 labels."""
        assert len(CANDIDATE_LABELS) == 3


class TestDisplaySortingProgress:
    """Tests for display_sorting_progress function."""

    def test_does_not_raise(self, capsys):
        """Should not raise exceptions."""
        display_sorting_progress("test.pdf", "Invoice", 30)
        captured = capsys.readouterr()
        assert "test.pdf" in captured.out
        assert "Invoice" in captured.out
        assert "30" in captured.out
