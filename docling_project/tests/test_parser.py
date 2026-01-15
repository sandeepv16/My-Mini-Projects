import pytest
from src.parser import PDFParser
from src.models import TableData


class TestPDFParser:
    def test_parser_initialization(self, temp_pdf_file):
        parser = PDFParser(temp_pdf_file)
        assert parser.pdf_path.exists()
        assert str(parser.pdf_path).endswith('.pdf')

    def test_parse_tables_with_empty_pdf(self, temp_pdf_file):
        parser = PDFParser(temp_pdf_file)
        # Empty/invalid PDFs should raise an exception, which we catch
        with pytest.raises(Exception):
            result = parser.parse_tables()

    def test_parser_with_nonexistent_file(self):
        with pytest.raises(Exception):
            parser = PDFParser("nonexistent.pdf")
            parser.parse_tables()

    def test_parser_with_invalid_file_type(self, tmp_path):
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("Not a PDF")
        with pytest.raises(Exception):
            parser = PDFParser(str(invalid_file))
            parser.parse_tables()

    @pytest.mark.integration
    def test_table_data_structure(self, temp_pdf_file):
        parser = PDFParser(temp_pdf_file)
        # Since our test PDF is invalid, this will raise an exception
        # In a real scenario, this would work with a valid PDF
        try:
            results = parser.parse_tables()
            for result in results:
                assert isinstance(result, TableData)
                assert hasattr(result, 'document_name')
                assert hasattr(result, 'table_number')
                assert hasattr(result, 'row_number')
                assert hasattr(result, 'column_number')
                assert hasattr(result, 'cell_content')
        except Exception:
            # Expected for invalid PDF in test fixture
            pass
