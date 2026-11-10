from openpyxl import load_workbook


def extract_excel_text(file_path):
    """
    Extract data from all worksheets in an Excel file.
    """

    workbook = load_workbook(
        filename=file_path,
        read_only=True,
        data_only=True
    )

    extracted_parts = []

    try:
        for sheet in workbook.worksheets:

            extracted_parts.append(
                f"\n--- Sheet: {sheet.title} ---"
            )

            for row in sheet.iter_rows(values_only=True):

                values = [
                    str(value)
                    for value in row
                    if value is not None
                ]

                if values:
                    extracted_parts.append(" | ".join(values))

        return "\n".join(extracted_parts)

    finally:
        workbook.close()