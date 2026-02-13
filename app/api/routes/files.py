from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.files import BatchUploadResult, DocumentOut
from app.services.document_service import DocumentService, DocumentServiceError
from app.services.vector_store import VectorStore


router = APIRouter(prefix="/api/files", tags=["files"])
vector_store = VectorStore()


@router.get("", response_model=list[DocumentOut])
def list_files(db: Session = Depends(get_db)) -> list[DocumentOut]:
    service = DocumentService(db, vector_store)
    return [DocumentOut.model_validate(row) for row in service.list_documents()]


@router.get("/{document_id}", response_model=DocumentOut)
def get_file(document_id: str, db: Session = Depends(get_db)) -> DocumentOut:
    service = DocumentService(db, vector_store)
    row = service.get_document(document_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentOut.model_validate(row)


@router.post("", response_model=BatchUploadResult)
async def upload_files(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> BatchUploadResult:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    service = DocumentService(db, vector_store)
    indexed: list[DocumentOut] = []
    failed: list[dict[str, str]] = []

    for file in files:
        try:
            row = await service.upload(file)
            indexed.append(DocumentOut.model_validate(row))
        except DocumentServiceError as exc:
            failed.append({"filename": file.filename or "unknown", "reason": str(exc)})

    return BatchUploadResult(indexed=indexed, failed=failed)


@router.put("/{document_id}", response_model=DocumentOut)
async def replace_file(
    document_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentOut:
    service = DocumentService(db, vector_store)
    try:
        row = await service.replace(document_id, file)
        return DocumentOut.model_validate(row)
    except DocumentServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{document_id}")
def delete_file(document_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    service = DocumentService(db, vector_store)
    try:
        service.delete(document_id)
        return {"message": "Document deleted."}
    except DocumentServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
