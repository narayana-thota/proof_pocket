import logging
import os
import shutil
import subprocess
import tempfile

import fitz

from app.storage.b2_storage import download_file


logger = logging.getLogger(__name__)

# A page with fewer than this many meaningful characters is treated as
# potentially scanned and sent through OCR. This is evaluated per page so
# mixed PDFs (some selectable pages and some scanned pages) are supported.
MIN_NATIVE_TEXT_CHARS = 40
OCR_DPI = 300
OCR_LANGUAGE = "eng"
OCR_TIMEOUT_SECONDS = 120


def _has_usable_native_text(text: str) -> bool:
    """Return True when a page contains enough selectable text to use."""
    if not isinstance(text, str):
        return False

    meaningful_characters = sum(
        1 for character in text
        if character.isalnum()
    )
    return meaningful_characters >= MIN_NATIVE_TEXT_CHARS


def _run_ocr(page: fitz.Page) -> str:
    """
    OCR one PDF page using the Tesseract executable.

    PyMuPDF renders the page, so no Poppler installation or Python imaging
    package is required. Tesseract must be installed in the backend image.
    """
    tesseract_path = shutil.which("tesseract")
    if not tesseract_path:
        raise RuntimeError(
            "OCR is required for this scanned PDF page, but Tesseract is "
            "not installed. Install the 'tesseract-ocr' system package "
            "in the backend Docker image and rebuild it."
        )

    image_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        ) as image_file:
            image_path = image_file.name

        scale = OCR_DPI / 72
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            alpha=False
        )
        pixmap.save(image_path)

        result = subprocess.run(
            [
                tesseract_path,
                image_path,
                "stdout",
                "-l",
                OCR_LANGUAGE,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=OCR_TIMEOUT_SECONDS,
        )

        if result.returncode != 0:
            error_message = (result.stderr or "").strip()
            raise RuntimeError(
                "Tesseract OCR failed"
                + (f": {error_message}" if error_message else ".")
            )

        return (result.stdout or "").strip()

    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"OCR exceeded the {OCR_TIMEOUT_SECONDS}-second page timeout."
        ) from error

    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


def extract_pdf_text(object_key):
    """
    Download a PDF from Backblaze B2 and extract text.

    Selectable text is extracted with PyMuPDF. Pages without enough native
    text are processed with Tesseract OCR. The return structure remains
    compatible with document_service.process_pdf_document().
    """
    if not isinstance(object_key, str) or not object_key.strip():
        raise ValueError("A valid Backblaze object key is required.")

    pdf_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False
        ) as pdf_file:
            pdf_path = pdf_file.name

        download_file(
            object_key=object_key,
            destination_path=pdf_path
        )

        with fitz.open(pdf_path) as pdf_document:
            if pdf_document.page_count == 0:
                raise ValueError("The uploaded PDF contains no pages.")

            page_texts = []
            ocr_pages = 0

            for page_number, page in enumerate(
                pdf_document,
                start=1
            ):
                native_text = (page.get_text("text") or "").strip()

                if _has_usable_native_text(native_text):
                    page_text = native_text
                    extraction_method = "native"
                else:
                    logger.info(
                        "Page %s has insufficient selectable text; "
                        "attempting OCR.",
                        page_number
                    )
                    ocr_text = _run_ocr(page)

                    # Prefer OCR when it returns more usable content.
                    if len(ocr_text.strip()) > len(native_text):
                        page_text = ocr_text
                    else:
                        page_text = native_text

                    extraction_method = "ocr"
                    ocr_pages += 1

                    if not page_text.strip():
                        logger.warning(
                            "No text could be extracted from PDF page %s.",
                            page_number
                        )

                logger.info(
                    "PDF page %s extracted using %s (%s characters).",
                    page_number,
                    extraction_method,
                    len(page_text)
                )

                page_texts.append(
                    f"\n--- Page {page_number} ---\n{page_text}"
                )

            extracted_text = "\n".join(page_texts).strip()

            if not extracted_text:
                raise ValueError(
                    "No text could be extracted from this PDF, including "
                    "OCR. The document may be blank, damaged, or require "
                    "a different OCR language."
                )

            logger.info(
                "PDF extraction completed: %s pages, %s OCR pages, "
                "%s extracted characters.",
                pdf_document.page_count,
                ocr_pages,
                len(extracted_text)
            )

            return {
                "extracted_text": extracted_text,
                "page_count": pdf_document.page_count
            }

    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)
