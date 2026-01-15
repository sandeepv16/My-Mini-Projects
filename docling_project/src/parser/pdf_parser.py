from pathlib import Path
from src.models.table_data import TableData


class PDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self._converter = None

    def _get_converter(self):
        """Lazy load DocumentConverter"""
        if self._converter is None:
            try:
                from docling.document_converter import DocumentConverter
                self._converter = DocumentConverter()
            except ImportError as e:
                raise ImportError(f"Failed to import DocumentConverter: {e}")
        return self._converter

    def parse_tables(self) -> list[TableData]:
        """
        Parse tables from PDF and return list of TableData objects
        Maps PDF columns 1-6 directly to database columns using column_number to track position
        Each row creates 6 TableData entries (one per column)
        """
        try:
            from datetime import datetime
            converter = self._get_converter()
            result = converter.convert(str(self.pdf_path))

            table_data_list = []

            # Helpers to extract metadata from docling document object
            def _get_meta_field(doc, possible_keys):
                # Check common metadata containers
                candidates = []
                if hasattr(doc, 'metadata'):
                    candidates.append(getattr(doc, 'metadata'))
                if hasattr(doc, 'info'):
                    candidates.append(getattr(doc, 'info'))
                if hasattr(doc, 'properties'):
                    candidates.append(getattr(doc, 'properties'))

                for c in candidates:
                    try:
                        if c is None:
                            continue
                        # dict-like
                        for k in possible_keys:
                            if isinstance(c, dict) and k in c and c[k]:
                                return c[k]
                            # some containers expose attributes
                            if hasattr(c, k) and getattr(c, k):
                                return getattr(c, k)
                    except Exception:
                        continue
                return None

            def _parse_pdf_date(s):
                if not s:
                    return None
                s = str(s).strip()
                # PDF date format starting with D:YYYYMMDD...
                if s.startswith('D:'):
                    try:
                        y = int(s[2:6])
                        m = int(s[6:8])
                        d = int(s[8:10])
                        hh = int(s[10:12]) if len(s) >= 12 else 0
                        mm = int(s[12:14]) if len(s) >= 14 else 0
                        # Normalize to MM-DD-YYYY HH:MM
                        return f"{m:02d}-{d:02d}-{y:04d} {hh:02d}:{mm:02d}"
                    except Exception:
                        pass
                # Try common ISO-like formats
                from datetime import datetime as _dt
                fmts = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M",
                    "%Y-%m-%d",
                    "%m-%d-%Y %H:%M:%S",
                    "%m-%d-%Y %H:%M",
                    "%m-%d-%Y",
                    "%m/%d/%Y",
                    "%d/%m/%Y",
                    "%d-%m-%Y",
                    "%d %B %Y",
                    "%B %d, %Y",
                ]
                for f in fmts:
                    try:
                        dt = _dt.strptime(s, f)
                        # Normalize to MM-DD-YYYY HH:MM (drop seconds)
                        hour = dt.hour
                        minute = dt.minute
                        return dt.strftime(f"%m-%d-%Y {hour:02d}:{minute:02d}")
                    except Exception:
                        continue

                # If nothing matched, don't return a bare year — treat as unknown
                return None

            def _normalize_and_combine_date_field(s, doc_date_str=None):
                """
                Normalize the 7th-column value. If it's time-only (e.g. "12:34" or "12:34:56" or "1:23 PM"),
                try to combine it with `doc_date_str` (which is the previously extracted document date)
                to produce a full `YYYY-MM-DD HH:MM:SS` string. If a full date is present already, parse
                and normalize via `_parse_pdf_date`.
                """
                if not s:
                    return None
                s = str(s).strip()
                import re
                # time-only patterns like 12:34 or 12:34:56 or 1:23 PM
                time_only_re = re.compile(r"^\s*\d{1,2}:\d{2}(:\d{2})?(\s?[APMapm]{2})?\s*$")
                if time_only_re.match(s):
                    # extract date part from doc_date_str if available (expects YYYY-MM-DD...)
                    date_part = None
                    if doc_date_str:
                        # Try to normalize doc_date_str first (it may be in various formats)
                        parsed_doc = _parse_pdf_date(doc_date_str)
                        if parsed_doc:
                            # parsed_doc is in MM-DD-YYYY HH:MM or MM-DD-YYYY HH:MM:SS-like format
                            date_part = str(parsed_doc).split()[0]
                        else:
                            # try to pull a 4-digit year as last resort
                            m2 = re.search(r"(20\d{2}|19\d{2})", str(doc_date_str))
                            if m2:
                                date_part = f"01-01-{m2.group(1)}"

                    # try to parse time and combine
                    from datetime import datetime as _dt
                    for tf in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"):
                        try:
                            t = _dt.strptime(s, tf)
                            time_part = t.strftime("%H:%M")
                            if date_part:
                                return f"{date_part} {time_part}"
                            # otherwise return normalized time-only string
                            return time_part
                        except Exception:
                            continue
                    return None

                # if it looks like a date or datetime, try to parse and normalize
                parsed = _parse_pdf_date(s)
                return parsed

            def _to_int_safe(value):
                if value is None:
                    return None
                s = str(value).strip()
                if s == "":
                    return None
                try:
                    return int(s)
                except Exception:
                    return None

            # Prefer metadata values from the converted document
            doc_obj = getattr(result, 'document', None)
            document_name = None
            extracted_date = None

            if doc_obj is not None:
                # Try common title/name fields
                document_name = _get_meta_field(doc_obj, ['Title', 'title', 'DocumentTitle', 'name'])
                # Try extracted title attribute
                if not document_name and hasattr(doc_obj, 'title') and getattr(doc_obj, 'title'):
                    document_name = getattr(doc_obj, 'title')

                # Extract creation/modification date from metadata
                date_val = _get_meta_field(doc_obj, ['CreationDate', 'ModDate', 'Created', 'created', 'Date', 'date'])
                if date_val:
                    extracted_date = _parse_pdf_date(date_val)

                # If still missing, try first page text for title/date hints
                if (not document_name or not extracted_date) and hasattr(doc_obj, 'pages') and doc_obj.pages:
                    try:
                        first_page = doc_obj.pages[0]
                        page_text = None
                        if hasattr(first_page, 'text'):
                            page_text = getattr(first_page, 'text')
                        elif hasattr(first_page, 'get_text'):
                            page_text = first_page.get_text()
                        if page_text:
                            # derive title as first non-empty line
                            if not document_name:
                                for line in str(page_text).splitlines():
                                    t = line.strip()
                                    if t:
                                        document_name = t[:255]
                                        break
                            # find a date-like substring
                            if not extracted_date:
                                import re
                                # look for YYYY-MM-DD / DD/MM/YYYY / Month DD, YYYY
                                m = re.search(r"(20\d{2}-\d{2}-\d{2})", page_text)
                                if not m:
                                    m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", page_text)
                                if not m:
                                    m = re.search(r"([A-Za-z]{3,9} \d{1,2}, \d{4})", page_text)
                                if m:
                                    extracted_date = _parse_pdf_date(m.group(1))
                    except Exception:
                        pass

            # Final fallbacks
            if not document_name:
                document_name = self.pdf_path.name
            if not extracted_date:
                extracted_date = None

            # Extract tables from the document
            for table_idx, table in enumerate(result.document.tables, 1):
                # Try to export table to dataframe for more reliable extraction
                try:
                    df = table.export_to_dataframe()
                    print(f"Table {table_idx}: {len(df)} rows, {len(df.columns)} columns")
                    print(f"Columns: {df.columns.tolist()}")
                    
                    # Iterate through data rows and create ONE TableData per PDF table row
                    # Keep last seen values per column to forward-fill missing entries
                    last_seen = [None] * 7
                    # materialize rows so we can look ahead for split date/time cells
                    # Build rows from dataframe. Some table.export_to_dataframe() calls
                    # use the first data row as the header, so detect that case and
                    # prepend the columns back as the first row to avoid skipping it.
                    try:
                        import pandas as _pd
                        is_range_index = isinstance(df.columns, _pd.RangeIndex)
                    except Exception:
                        is_range_index = False

                    if is_range_index:
                        df_rows = [
                            [str(cell).strip() if cell is not None and str(cell).strip() != 'nan' else "" for cell in r]
                            for r in df.itertuples(index=False)
                        ]
                    else:
                        # columns appear to have been set from the first data row; include them
                        header_row = [str(c).strip() if c is not None and str(c).strip() != 'nan' else "" for c in df.columns]
                        body_rows = [
                            [str(cell).strip() if cell is not None and str(cell).strip() != 'nan' else "" for cell in r]
                            for r in df.itertuples(index=False)
                        ]
                        # If the first body row appears to be the same as the inferred header row,
                        # skip it to avoid duplication. Treat both exact equality, prefix match,
                        # and header-keyword detection as indicators of a duplicated header.
                        def _looks_like_header_row(row):
                            """Return True if row[0] or row[1] contain header-like keywords."""
                            keywords = {'id', 'document', 'table', 'row', 'column', 'cell', 'content', 'date', 'name', 'number', 'extracted'}
                            for idx in range(min(2, len(row))):
                                val = str(row[idx]).lower().strip()
                                if val in keywords or any(kw in val for kw in keywords):
                                    return True
                            return False

                        if body_rows:
                            min_len = min(len(body_rows[0]), len(header_row))
                            is_exact = len(body_rows[0]) == len(header_row) and body_rows[0] == header_row
                            is_prefix = False
                            if min_len >= 2:
                                try:
                                    is_prefix = all(str(body_rows[0][i]) == str(header_row[i]) for i in range(min_len))
                                except Exception:
                                    is_prefix = False
                            is_header_like = _looks_like_header_row(body_rows[0])
                            if is_exact or is_prefix or is_header_like:
                                df_rows = [header_row] + body_rows[1:]
                            else:
                                df_rows = [header_row] + body_rows
                        else:
                            df_rows = [header_row] + body_rows

                    def _is_time_only(s):
                        if not s:
                            return False
                        import re
                        return bool(re.match(r"^\s*\d{1,2}:\d{2}(:\d{2})?(\s?[APMapm]{2})?\s*$", s))

                    def _is_date_like_without_time(s):
                        if not s:
                            return False
                        # if it contains a colon it's not date-only
                        if ":" in s:
                            return False
                        import re
                        # common date patterns like MM-DD-YYYY, YYYY-MM-DD, DD/MM/YYYY
                        return bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|[A-Za-z]{3,9} \d{1,2}, \d{4}", s))

                    def _strip_trailing_date(s):
                        """Remove trailing date patterns (e.g. ' 10-01-2026') from string."""
                        if not s:
                            return s
                        import re
                        # patterns: MM-DD-YYYY, YYYY-MM-DD, DD/MM/YYYY etc at end of string
                        pattern = r"\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2})$"
                        return re.sub(pattern, "", s)

                    prev_seventh = None
                    for row_idx, row_values in enumerate(df_rows, 1):
                        # Skip the header row only for the first table (table_idx == 1)
                        if table_idx == 1 and row_idx == 1:
                            continue
                        # Process all other rows
                        # If table has 8 columns where 7th is date-only and 8th is time-only,
                        # merge them into a single 7th column to avoid losing the time column
                        # when truncating to 7 columns later.
                        try:
                            if len(row_values) >= 8:
                                if _is_date_like_without_time(row_values[6]) and _is_time_only(row_values[7]):
                                    # keep date as-is but append time part
                                    import re
                                    tm = re.search(r"(\d{1,2}:\d{2})", row_values[7])
                                    if tm:
                                        row_values[6] = f"{row_values[6]} {tm.group(1)}"
                                    else:
                                        row_values[6] = f"{row_values[6]} {row_values[7]}"
                                    # remove the now-merged 8th column
                                    del row_values[7]
                        except Exception:
                            pass
                        # Ensure we have at least 7 values (pad with empty strings if needed)
                        while len(row_values) < 7:
                            row_values.append("")

                        # Truncate if more than 7 columns
                        row_values = row_values[:7]

                        # Forward-fill missing values from last seen values (do not apply other defaults)
                        for i in range(7):
                            if (not row_values[i]) and last_seen[i] is not None:
                                row_values[i] = last_seen[i]

                        # Map fields per request:
                        # document_name <- 2nd column (index 1)
                        # cell_content  <- 6th column (index 5)
                        # extracted_date<- 7th column (index 6) or fallback
                        second_col_value = row_values[1] if len(row_values) >= 2 and row_values[1] else ""
                        
                        # Validate document_name: if it's just a number or doesn't look like a filename, use last seen or PDF name
                        def _is_valid_document_name(s):
                            if not s:
                                return False
                            s = str(s).strip()
                            # If it's purely numeric, it's not valid
                            if s.isdigit():
                                return False
                            # If it contains a file extension or has letters, it's likely valid
                            if '.' in s or any(c.isalpha() for c in s):
                                return True
                            return False
                        
                        if not _is_valid_document_name(second_col_value):
                            # Use last seen valid document name from parsed data
                            if last_seen[1] and _is_valid_document_name(last_seen[1]):
                                second_col_value = last_seen[1]
                        
                        third_col_value = row_values[2] if len(row_values) >= 3 else ""
                        fourth_col_value = row_values[3] if len(row_values) >= 4 else ""
                        fifth_col_value = row_values[4] if len(row_values) >= 5 else ""
                        sixth_col_value = _strip_trailing_date(row_values[5]) if len(row_values) >= 6 else ""

                        raw_seventh = row_values[6] if len(row_values) >= 7 and row_values[6] else None

                        # Combine date and time across rows
                        combined_value = None
                        if _is_time_only(raw_seventh) and prev_seventh:
                            # time-only, try to get date from previous row's seventh
                            parsed_date = _parse_pdf_date(prev_seventh)
                            if parsed_date:
                                date_part = str(parsed_date).split()[0]
                                import re
                                tmatch = re.search(r"(\d{1,2}:\d{2})", raw_seventh)
                                if tmatch:
                                    combined_value = f"{date_part} {tmatch.group(1)}"
                        elif _is_date_like_without_time(raw_seventh) and (row_idx < len(df_rows)):
                            # date-only, take time from next row
                            next_raw = df_rows[row_idx][6] if len(df_rows[row_idx]) >= 7 else None
                            if _is_time_only(next_raw):
                                parsed_date = _parse_pdf_date(raw_seventh)
                                if parsed_date:
                                    date_part = str(parsed_date).split()[0]
                                    import re
                                    tmatch = re.search(r"(\d{1,2}:\d{2})", next_raw)
                                    if tmatch:
                                        combined_value = f"{date_part} {tmatch.group(1)}"
                                        # set next row's seventh to combined
                                        df_rows[row_idx][6] = combined_value

                        # Normalize/merge time-only 7th-column values with document-level `extracted_date` when possible
                        if combined_value:
                            seventh_col_value = combined_value
                        else:
                            seventh_col_value = _normalize_and_combine_date_field(raw_seventh, extracted_date)

                        table_data = TableData(
                            document_name=second_col_value,
                            table_number=_to_int_safe(third_col_value),
                            row_number=_to_int_safe(fourth_col_value),
                            column_number=_to_int_safe(fifth_col_value),
                            cell_content=sixth_col_value,
                            extracted_date=seventh_col_value
                        )
                        table_data_list.append(table_data)
                        prev_seventh = seventh_col_value
                        # If this is the first table and first row, print column values for debugging
                        if table_idx == 1 and row_idx == 1:
                            print("First row columns (from dataframe):")
                            for col_idx, val in enumerate(row_values, start=1):
                                print(f"  Column {col_idx}: {val}")
                        # If this is the first table and third row, print column values for debugging
                        if table_idx == 1 and row_idx == 3:
                            print("Third row columns (from dataframe):")
                            for col_idx, val in enumerate(row_values, start=1):
                                print(f"  Column {col_idx}: {val}")
                        # Update last seen values
                        for i in range(7):
                            if row_values[i]:
                                # For document_name (index 1), only update if it's a valid name
                                if i == 1:
                                    if _is_valid_document_name(row_values[i]):
                                        last_seen[i] = row_values[i]
                                else:
                                    last_seen[i] = row_values[i]
                        
                except (AttributeError, Exception) as e:
                    print(f"Could not export to dataframe for table {table_idx}, trying alternative method: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback: use data attribute
                    if hasattr(table, 'data'):
                        # Fallback: use table.data and forward-fill missing values per table
                        last_seen = [None] * 7
                        prev_seventh = None
                        for row_idx, row in enumerate(table.data, 1):
                            row_values = []
                            for cell in row:
                                cell_text = ""
                                if isinstance(cell, str):
                                    cell_text = cell.strip()
                                elif hasattr(cell, 'text'):
                                    cell_text = str(cell.text).strip() if cell.text else ""
                                else:
                                    cell_text = str(cell).strip()
                                row_values.append(cell_text)

                            # Skip the header row only for the first table (table_idx == 1)
                            if table_idx == 1 and row_idx == 1:
                                continue

                            # If table has 8 columns where 7th is date-only and 8th is time-only,
                            # merge them into a single 7th column to avoid losing the time column
                            # when truncating to 7 columns later.
                            try:
                                if len(row_values) >= 8:
                                    import re
                                    date_like = bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|[A-Za-z]{3,9} \d{1,2}, \d{4}", str(row_values[6])))
                                    time_only = bool(re.match(r"^\s*\d{1,2}:\d{2}(:\d{2})?(\s?[APMapm]{2})?\s*$", str(row_values[7])))
                                    if date_like and time_only:
                                        tm = re.search(r"(\d{1,2}:\d{2})", row_values[7])
                                        if tm:
                                            row_values[6] = f"{row_values[6]} {tm.group(1)}"
                                        else:
                                            row_values[6] = f"{row_values[6]} {row_values[7]}"
                                        del row_values[7]
                            except Exception:
                                pass

                            # Ensure we have at least 7 values (pad with empty strings if needed)
                            while len(row_values) < 7:
                                row_values.append("")

                            # Truncate if more than 7 columns
                            row_values = row_values[:7]

                        # After truncation/merging, ensure we still have 7 columns
                        while len(row_values) < 7:
                            row_values.append("")

                            # Forward-fill missing values from last seen values (do not apply other defaults)
                            for i in range(7):
                                if (not row_values[i]) and last_seen[i] is not None:
                                    row_values[i] = last_seen[i]

                            # Map fields per request
                            second_col_value = row_values[1] if len(row_values) >= 2 and row_values[1] else ""
                            
                            # Validate document_name: if it's just a number or doesn't look like a filename, use last seen or PDF name
                            def _is_valid_document_name_local(s):
                                if not s:
                                    return False
                                s = str(s).strip()
                                # If it's purely numeric, it's not valid
                                if s.isdigit():
                                    return False
                                # If it contains a file extension or has letters, it's likely valid
                                if '.' in s or any(c.isalpha() for c in s):
                                    return True
                                return False
                            
                            if not _is_valid_document_name_local(second_col_value):
                                # Use last seen valid document name from parsed data
                                if last_seen[1] and _is_valid_document_name_local(last_seen[1]):
                                    second_col_value = last_seen[1]
                            
                            third_col_value = row_values[2] if len(row_values) >= 3 else ""
                            fourth_col_value = row_values[3] if len(row_values) >= 4 else ""
                            fifth_col_value = row_values[4] if len(row_values) >= 5 else ""
                            sixth_col_value = _strip_trailing_date_local(row_values[5]) if len(row_values) >= 6 else ""
                            raw_seventh = row_values[6] if len(row_values) >= 7 and row_values[6] else None

                            # local helpers for fallback
                            def _is_time_only_local(s):
                                if not s:
                                    return False
                                import re
                                return bool(re.match(r"^\s*\d{1,2}:\d{2}(:\d{2})?(\s?[APMapm]{2})?\s*$", s))

                            def _is_date_like_without_time_local(s):
                                if not s:
                                    return False
                                if ":" in s:
                                    return False
                                import re
                                return bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|[A-Za-z]{3,9} \d{1,2}, \d{4}", s))

                            def _strip_trailing_date_local(s):
                                """Remove trailing date patterns (e.g. ' 10-01-2026') from string."""
                                if not s:
                                    return s
                                import re
                                pattern = r"\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2})$"
                                return re.sub(pattern, "", s)

                            # If this row is date-only and next row is time-only, combine them
                            combined_value = None
                            if _is_time_only_local(raw_seventh) and prev_seventh:
                                parsed_date = _parse_pdf_date(prev_seventh)
                                if parsed_date:
                                    date_part = str(parsed_date).split()[0]
                                    import re
                                    tmatch = re.search(r"(\d{1,2}:\d{2})", raw_seventh)
                                    if tmatch:
                                        combined_value = f"{date_part} {tmatch.group(1)}"
                            elif _is_date_like_without_time_local(raw_seventh) and (row_idx < len(table.data)):
                                try:
                                    next_row = table.data[row_idx]
                                    next_raw = None
                                    if len(next_row) >= 7:
                                        c = next_row[6]
                                        if isinstance(c, str):
                                            next_raw = c.strip()
                                        elif hasattr(c, 'text'):
                                            next_raw = str(c.text).strip()
                                        else:
                                            next_raw = str(c).strip()
                                    if _is_time_only_local(next_raw):
                                        parsed_date = _parse_pdf_date(raw_seventh)
                                        if parsed_date:
                                            date_part = str(parsed_date).split()[0]
                                            import re
                                            tmatch = re.search(r"(\d{1,2}:\d{2})", next_raw)
                                            if tmatch:
                                                combined_value = f"{date_part} {tmatch.group(1)}"
                                                # set next row's 7th cell to combined
                                                try:
                                                    if len(next_row) >= 7:
                                                        if isinstance(next_row[6], str):
                                                            next_row[6] = combined_value
                                                except Exception:
                                                    pass
                                except Exception:
                                    pass

                            seventh_col_value = combined_value if combined_value else _normalize_and_combine_date_field(raw_seventh, extracted_date)

                            table_data = TableData(
                            document_name=second_col_value,
                            table_number=_to_int_safe(third_col_value),
                            row_number=_to_int_safe(fourth_col_value),
                            column_number=_to_int_safe(fifth_col_value),
                            cell_content=sixth_col_value,
                            extracted_date=seventh_col_value
                            )
                            table_data_list.append(table_data)
                            prev_seventh = seventh_col_value
                            # If this is the first table and first row, print column values for debugging
                            if table_idx == 1 and row_idx == 1:
                                print("First row columns (fallback):")
                                for col_idx, val in enumerate(row_values, start=1):
                                    print(f"  Column {col_idx}: {val}")
                            # If this is the first table and third row, print column values for debugging
                            if table_idx == 1 and row_idx == 3:
                                print("Third row columns (fallback):")
                                for col_idx, val in enumerate(row_values, start=1):
                                    print(f"  Column {col_idx}: {val}")
                            # Update last seen values
                            for i in range(7):
                                if row_values[i]:
                                    # For document_name (index 1), only update if it's a valid name
                                    if i == 1:
                                        if _is_valid_document_name_local(row_values[i]):
                                            last_seen[i] = row_values[i]
                                    else:
                                        last_seen[i] = row_values[i]

            print(f"Total rows extracted: {len(table_data_list)}")
            return table_data_list
        except Exception as e:
            print(f"Error parsing PDF {self.pdf_path}: {e}")
            import traceback
            traceback.print_exc()
            raise

