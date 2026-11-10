def extract_txt_text(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        errors="replace"
    ) as file:

        extracted_text = file.read()

    return extracted_text