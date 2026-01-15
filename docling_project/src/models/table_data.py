from dataclasses import dataclass
from typing import Optional


@dataclass
class TableData:
    document_name: str
    table_number: int
    row_number: int
    column_number: int
    cell_content: str
    extracted_date: Optional[str] = None
