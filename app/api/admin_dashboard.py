"""
Admin API endpoints for Knowledge Base Dashboard
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import csv
import json
from io import StringIO

from app.dependencies import require_admin

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get("/documents")
async def get_documents(
    page: int = 1,
    page_size: int = 25,
    sort_field: str = "upload_timestamp",
    sort_order: str = "desc",
    search: str = "",
    admin: dict = Depends(require_admin)
):
    """
    Get paginated, searchable, sortable document list (admin only).
    
    Returns document metadata with filtering and sorting capabilities.
    """
    # Mock data (in production, query database)
    documents = [
        {
            "document_id": f"doc_{i}",
            "filename": f"financial_report_{i}.pdf",
            "file_size_bytes": 1024000 + i * 1000,
            "upload_timestamp": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(),
            "processing_status": "completed" if i % 3 == 0 else "processing" if i % 3 == 1 else "failed",
            "uploaded_by": "admin" if i % 2 == 0 else "johndoe",
            "content_type": "application/pdf"
        }
        for i in range(1, 51)
    ]
    
    # Apply search filter
    if search:
        documents = [d for d in documents if search.lower() in d["filename"].lower()]
    
    # Apply sorting
    reverse = sort_order == "desc"
    documents.sort(key=lambda x: x.get(sort_field, ""), reverse=reverse)
    
    # Apply pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated = documents[start:end]
    
    return {
        "documents": paginated,
        "total": len(documents),
        "page": page,
        "page_size": page_size,
        "total_pages": (len(documents) + page_size - 1) // page_size
    }


@router.get("/statistics")
async def get_statistics(admin: dict = Depends(require_admin)):
    """Get document statistics (admin only)"""
    return {
        "total_documents": 15420,
        "by_type": {
            "PDF": 8500,
            "Word": 4200,
            "Text": 2100,
            "CSV": 620
        },
        "by_status": {
            "completed": 14850,
            "processing": 420,
            "failed": 150
        },
        "by_stage": {
            "indexed": 14850,
            "embedding": 320,
            "extraction": 100,
            "uploaded": 150
        }
    }


@router.get("/export")
async def export_data(
    format: str = "csv",
    admin: dict = Depends(require_admin)
):
    """Export dashboard data (admin only)"""
    # Mock data
    documents = [
        {
            "document_id": f"doc_{i}",
            "filename": f"report_{i}.pdf",
            "file_size_bytes": 1024000,
            "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_status": "completed",
            "uploaded_by": "admin"
        }
        for i in range(1, 101)
    ]
    
    if format == "csv":
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=documents[0].keys())
        writer.writeheader()
        writer.writerows(documents)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=knowledge-base-{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    
    elif format == "json":
        return Response(
            content=json.dumps(documents, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=knowledge-base-{datetime.now().strftime('%Y%m%d')}.json"
            }
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'")

