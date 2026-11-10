import logging

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException
)

from app.dependencies import get_current_user
from app.services.document_indexing_service import index_document
from app.services.document_service import (
    upload_document,
    get_user_documents,
    get_document_by_id,
    get_document_download_url,
    delete_document,
    process_pdf_document,
    process_docx_document,
    process_excel_document,
    process_txt_document
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


@router.post("/upload", status_code=201)
def upload_document_route(
    file: UploadFile = File(...),
    category_id: int | None = Form(None),
    document_type: str | None = Form(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        result = upload_document(
            user_id=current_user["user_id"],
            uploaded_file=file,
            category_id=category_id,
            document_type=document_type
        )
        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        logger.exception("Document upload failed")
        raise HTTPException(
            status_code=500,
            detail="Document upload failed. Check backend logs."
        )

    finally:
        file.file.close()


@router.get("/")
def list_documents(
    current_user: dict = Depends(get_current_user)
):
    try:
        return get_user_documents(user_id=current_user["user_id"])

    except Exception:
        logger.exception("Failed to retrieve documents")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve documents."
        )


@router.get("/{document_id}")
def get_document_details(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        document = get_document_by_id(
            document_id=document_id,
            user_id=current_user["user_id"]
        )

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        return {
            "success": True,
            "document": document
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to retrieve document details")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve document details."
        )


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = get_document_download_url(
            document_id=document_id,
            user_id=current_user["user_id"]
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        return {
            "success": True,
            "message": "Download URL generated successfully.",
            "document": result
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Document download failed")
        raise HTTPException(
            status_code=500,
            detail="Could not generate document download URL."
        )


@router.delete("/{document_id}")
def remove_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = delete_document(
            document_id=document_id,
            user_id=current_user["user_id"]
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        return {
            "success": True,
            "message": "Document deleted successfully.",
            "document_id": result["document_id"],
            "storage_deleted": result["storage_deleted"]
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Document deletion failed")
        raise HTTPException(
            status_code=500,
            detail="Could not delete document."
        )


@router.post("/{document_id}/extract")
def extract_document_text(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = extract_and_index(
            extraction_function=process_pdf_document,
            document_id=document_id,
            user_id=current_user["user_id"]
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("PDF text extraction failed")
        raise HTTPException(
            status_code=500,
            detail="PDF text extraction failed."
        )


@router.post("/{document_id}/extract-docx")
def extract_docx_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = extract_and_index(
            extraction_function=process_docx_document,
            document_id=document_id,
            user_id=current_user["user_id"]
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("DOCX extraction failed")
        raise HTTPException(
            status_code=500,
            detail="DOCX extraction failed."
        )


@router.post("/{document_id}/extract-excel")
def extract_excel_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = extract_and_index(
            extraction_function=process_excel_document,
            document_id=document_id,
            user_id=current_user["user_id"]
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("Excel text extraction failed")
        raise HTTPException(
            status_code=500,
            detail="Excel text extraction failed."
        )


@router.post("/{document_id}/extract-txt")
def extract_txt_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = extract_and_index(
            extraction_function=process_txt_document,
            document_id=document_id,
            user_id=current_user["user_id"]
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("TXT text extraction failed")
        raise HTTPException(
            status_code=500,
            detail="TXT text extraction failed."
        )


def extract_and_index(
    extraction_function,
    document_id: int,
    user_id: int
):
    # Step 1: Extract document text.
    extraction_result = extraction_function(
        document_id=document_id,
        user_id=user_id
    )

    if not extraction_result:
        return None

    # Step 2: Index the extracted text for document Q&A.
    indexing_result = index_document(
        document_id=document_id,
        user_id=user_id
    )

    # Step 3: Generate AI reminder suggestions.
    # Reminder generation is deliberately isolated: if the LLM or
    # suggestion persistence fails, successful extraction/indexing
    # must remain successful.
    reminder_result = None

    try:
        from app.services.ai_reminder_service import (
            generate_document_reminder_suggestions
        )

        reminder_result = generate_document_reminder_suggestions(
            user_id=user_id,
            document_id=document_id
        )

    except Exception:
        logger.exception(
            "AI reminder suggestion generation failed for document_id=%s",
            document_id
        )
        reminder_result = {
            "success": False,
            "document_id": document_id,
            "total": 0,
            "suggestions": [],
            "message": (
                "Document extraction and indexing completed, "
                "but AI reminder suggestions could not be generated."
            )
        }

    # Step 4: Return extraction, indexing, and reminder results.
    if isinstance(extraction_result, dict):
        return {
            **extraction_result,
            "indexing": indexing_result,
            "reminder_suggestions": reminder_result
        }

    return {
        "extraction": extraction_result,
        "indexing": indexing_result,
        "reminder_suggestions": reminder_result
    }
