import os
from config.config import PDF_INPUT_PATH
from src.database.db_operations import DatabaseOperations


def main():
    try:
        # Import PDFParser here to catch import errors
        from src.parser import PDFParser
        
        # Create PDF input directory if it doesn't exist
        os.makedirs(PDF_INPUT_PATH, exist_ok=True)

        # Initialize database operations
        db_ops = DatabaseOperations()

        # Process each PDF in the input directory
        for pdf_file in os.listdir(PDF_INPUT_PATH):
            if pdf_file.lower().endswith('.pdf'):
                pdf_path = os.path.join(PDF_INPUT_PATH, pdf_file)

                # Parse PDF tables
                parser = PDFParser(pdf_path)
                table_data_list = parser.parse_tables()

                # Insert parsed data into database
                if table_data_list:
                    db_ops.insert_table_data(table_data_list)
                    print(f"Successfully processed {pdf_file}")
                else:
                    print(f"No table data found in {pdf_file}")

    except Exception as e:
        print(f"Error in main process: {e}")


if __name__ == "__main__":
    main()
