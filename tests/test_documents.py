"""Tests for the documents module."""

import os
import tempfile
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock

import pytest

# Import the module functions
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from documents import (
    generate_random_date,
    create_pdf,
    setup_output_directory,
    generate_sample_documents,
    INVOICES,
    PROTOCOLS,
    REPORTS,
)


class TestGenerateRandomDate:
    """Tests for generate_random_date function."""

    def test_returns_datetime(self):
        """Should return a datetime object."""
        result = generate_random_date(2024)
        assert isinstance(result, datetime)

    def test_year_is_correct(self):
        """Should return date in the specified year."""
        result = generate_random_date(2024)
        assert result.year == 2024

    def test_date_within_year(self):
        """Should return date within January 1 to December 31."""
        for _ in range(100):  # Test multiple times for randomness
            result = generate_random_date(2024)
            assert result >= datetime(2024, 1, 1)
            assert result <= datetime(2024, 12, 31)

    def test_different_years(self):
        """Should work for different years."""
        for year in [2020, 2023, 2024, 2030]:
            result = generate_random_date(year)
            assert result.year == year

    def test_invalid_year_low(self):
        """Should raise ValueError for year < 1."""
        with pytest.raises(ValueError):
            generate_random_date(0)

    def test_invalid_year_high(self):
        """Should raise ValueError for year > 9999."""
        with pytest.raises(ValueError):
            generate_random_date(10000)


class TestSampleDocumentContent:
    """Tests for sample document content."""

    def test_invoices_not_empty(self):
        """Should have invoice content."""
        assert len(INVOICES) > 0

    def test_protocols_not_empty(self):
        """Should have protocol content."""
        assert len(PROTOCOLS) > 0

    def test_reports_not_empty(self):
        """Should have report content."""
        assert len(REPORTS) > 0

    def test_invoices_are_strings(self):
        """All invoices should be strings."""
        for invoice in INVOICES:
            assert isinstance(invoice, str)
            assert len(invoice) > 0

    def test_protocols_are_strings(self):
        """All protocols should be strings."""
        for protocol in PROTOCOLS:
            assert isinstance(protocol, str)
            assert len(protocol) > 0

    def test_reports_are_strings(self):
        """All reports should be strings."""
        for report in REPORTS:
            assert isinstance(report, str)
            assert len(report) > 0


class TestCreatePdf:
    """Tests for create_pdf function."""

    @patch('documents.canvas.Canvas')
    def test_creates_pdf_file(self, mock_canvas_class):
        """Should create a PDF file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('documents.OUTPUT_DIR', tmpdir):
                mock_canvas = MagicMock()
                mock_canvas_class.return_value = mock_canvas

                test_date = datetime(2024, 6, 15)
                result = create_pdf(
                    "Test",
                    "Test content",
                    "test_doc",
                    test_date
                )

                assert result == "Test_2024-06-15"
                mock_canvas.save.assert_called_once()

    @patch('documents.canvas.Canvas')
    def test_correct_content_drawn(self, mock_canvas_class):
        """Should draw correct content on canvas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('documents.OUTPUT_DIR', tmpdir):
                mock_canvas = MagicMock()
                mock_canvas_class.return_value = mock_canvas

                test_date = datetime(2024, 6, 15)
                create_pdf("Invoice", "Test content", "test_doc", test_date)

                # Check that drawString was called
                assert mock_canvas.drawString.called
                calls = mock_canvas.drawString.call_args_list

                # Should have at least 5 drawString calls
                assert len(calls) >= 5

    @patch('documents.canvas.Canvas')
    def test_handles_long_content(self, mock_canvas_class):
        """Should truncate long content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('documents.OUTPUT_DIR', tmpdir):
                mock_canvas = MagicMock()
                mock_canvas_class.return_value = mock_canvas

                long_content = "x" * 200
                test_date = datetime(2024, 6, 15)
                create_pdf("Test", long_content, "test_doc", test_date)

                # Should not raise exception
                mock_canvas.save.assert_called_once()


class TestSetupOutputDirectory:
    """Tests for setup_output_directory function."""

    def test_creates_directory_if_not_exists(self):
        """Should create directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_output")
            with patch('documents.OUTPUT_DIR', new_dir):
                setup_output_directory()
                assert os.path.exists(new_dir)

    def test_does_not_fail_if_exists(self):
        """Should not fail if directory already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('documents.OUTPUT_DIR', tmpdir):
                # Should not raise
                setup_output_directory()
                assert os.path.exists(tmpdir)


class TestGenerateSampleDocuments:
    """Tests for generate_sample_documents function."""

    @patch('documents.create_pdf')
    @patch('documents.setup_output_directory')
    def test_generates_correct_count(self, mock_setup, mock_create_pdf):
        """Should generate the specified number of documents."""
        mock_create_pdf.return_value = "test_file"

        total = generate_sample_documents(
            num_invoices=2,
            num_protocols=2,
            num_reports=2,
            year=2024
        )

        assert total == 6
        assert mock_create_pdf.call_count == 6

    @patch('documents.create_pdf')
    @patch('documents.setup_output_directory')
    def test_default_counts(self, mock_setup, mock_create_pdf):
        """Should use default counts (4+3+3=10)."""
        mock_create_pdf.return_value = "test_file"

        total = generate_sample_documents()

        assert total == 10
        assert mock_create_pdf.call_count == 10

    @patch('documents.create_pdf')
    @patch('documents.setup_output_directory')
    def test_calls_setup_directory(self, mock_setup, mock_create_pdf):
        """Should call setup_output_directory."""
        mock_create_pdf.return_value = "test_file"

        generate_sample_documents(num_invoices=1, num_protocols=0, num_reports=0)

        mock_setup.assert_called_once()

    @patch('documents.create_pdf')
    @patch('documents.setup_output_directory')
    def test_zero_documents(self, mock_setup, mock_create_pdf):
        """Should handle zero document count."""
        total = generate_sample_documents(
            num_invoices=0,
            num_protocols=0,
            num_reports=0
        )

        assert total == 0
        mock_create_pdf.assert_not_called()
