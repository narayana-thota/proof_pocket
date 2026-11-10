from docx import Document


def extract_docx_text(file_path):
    """
    Extract text from paragraphs and tables in a DOCX file.
    """

    document = Document(file_path)

    extracted_parts = []

    # Extract paragraph text
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            extracted_parts.append(text)

    # Extract table text
    for table in document.tables:
        for row in table.rows:
            row_text = " | ".join(
                cell.text.strip() for cell in row.cells
            )

            if row_text.strip():
                extracted_parts.append(row_text)

    return "\n".join(extracted_parts)