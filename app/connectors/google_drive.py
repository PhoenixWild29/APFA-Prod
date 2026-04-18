"""Google Drive connector for the APFA data pipeline.

Syncs documents from shared Google Drive folders into the RAG corpus.
Supports: Google Docs (→ Markdown/TXT), PDFs (→ pypdf), Sheets (→ CSV
via Sheets API), plain text files.

Change detection: polling with changes.getStartPageToken + changes.list.
Only re-embeds chunks whose content hash changed.

SECURITY:
- Service account auth scoped read-only to a single shared folder
- Rotate credentials quarterly
- Admin-only — never extend to end users
- Per-source audit log on every write
"""

import io
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.connectors.base import NormalizedRecord, RAGSource
from app.services.chunking import chunk_prose, chunk_regulatory, chunk_spreadsheet

logger = logging.getLogger(__name__)

# MIME types we can process
SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.google-apps.document": "gdoc",
    "application/vnd.google-apps.spreadsheet": "gsheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "txt",
    "text/csv": "txt",
}

# Google Docs export as plain text
EXPORT_MIME = "text/plain"


class GoogleDriveConnector(RAGSource):
    """Sync documents from Google Drive into the RAG pipeline.

    Uses a service account with read-only access to a shared folder.
    The folder must be explicitly shared with the service account email.
    """

    source_type = "google_drive"

    def __init__(self, credentials_json: str):
        """Initialize with service account credentials.

        Args:
            credentials_json: Path to service account JSON key file,
                or the JSON string itself.
        """
        self._creds_source = credentials_json
        self._service = None
        self._sheets_service = None

    def _get_drive_service(self):
        if self._service is not None:
            return self._service

        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/drive.readonly"]

        # Accept either a file path or raw JSON
        try:
            creds = service_account.Credentials.from_service_account_file(
                self._creds_source, scopes=scopes
            )
        except (FileNotFoundError, ValueError):
            info = json.loads(self._creds_source)
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=scopes
            )

        self._service = build("drive", "v3", credentials=creds)
        return self._service

    def _get_sheets_service(self):
        if self._sheets_service is not None:
            return self._sheets_service

        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

        try:
            creds = service_account.Credentials.from_service_account_file(
                self._creds_source, scopes=scopes
            )
        except (FileNotFoundError, ValueError):
            info = json.loads(self._creds_source)
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=scopes
            )

        self._sheets_service = build("sheets", "v4", credentials=creds)
        return self._sheets_service

    def fetch(
        self,
        folder_ids: list[str] | None = None,
        file_ids: list[str] | None = None,
        page_token: str | None = None,
    ) -> list[dict]:
        """Fetch documents from Google Drive.

        Args:
            folder_ids: List of Drive folder IDs to scan.
            file_ids: Specific file IDs to fetch (overrides folder_ids).
            page_token: Changes page token for incremental sync.

        Returns:
            List of raw document dicts with keys:
            id, name, mimeType, modifiedTime, text, webViewLink
        """
        service = self._get_drive_service()
        raw_docs = []

        if file_ids:
            for fid in file_ids:
                doc = self._fetch_single_file(service, fid)
                if doc:
                    raw_docs.append(doc)
            return raw_docs

        if not folder_ids:
            logger.warning("No folder_ids or file_ids provided")
            return []

        for folder_id in folder_ids:
            docs = self._list_folder_files(service, folder_id)
            for file_meta in docs:
                doc = self._extract_text(service, file_meta)
                if doc:
                    raw_docs.append(doc)

        return raw_docs

    def _list_folder_files(self, service, folder_id: str) -> list[dict]:
        """List all supported files in a folder (non-recursive)."""
        mime_filter = " or ".join(
            f"mimeType='{mt}'" for mt in SUPPORTED_MIME_TYPES
        )
        query = f"'{folder_id}' in parents and ({mime_filter}) and trashed=false"

        files = []
        page_token = None
        while True:
            resp = (
                service.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)",
                    pageSize=100,
                    pageToken=page_token,
                )
                .execute()
            )
            files.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        logger.info(f"Found {len(files)} files in folder {folder_id}")
        return files

    def _fetch_single_file(self, service, file_id: str) -> dict | None:
        """Fetch a single file by ID."""
        meta = (
            service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, webViewLink",
            )
            .execute()
        )
        return self._extract_text(service, meta)

    def _extract_text(self, service, file_meta: dict) -> dict | None:
        """Extract text content from a Drive file."""
        mime = file_meta["mimeType"]
        file_id = file_meta["id"]
        name = file_meta["name"]

        if mime not in SUPPORTED_MIME_TYPES:
            logger.debug(f"Skipping unsupported type {mime}: {name}")
            return None

        file_type = SUPPORTED_MIME_TYPES[mime]
        text = ""

        try:
            if file_type == "gdoc":
                # Export Google Doc as plain text
                content = (
                    service.files()
                    .export(fileId=file_id, mimeType=EXPORT_MIME)
                    .execute()
                )
                text = content.decode("utf-8") if isinstance(content, bytes) else content

            elif file_type == "gsheet":
                # Use Sheets API for structured extraction
                text = self._extract_spreadsheet(file_id, name)

            elif file_type == "pdf":
                # Download and extract via pypdf
                content = (
                    service.files()
                    .get_media(fileId=file_id)
                    .execute()
                )
                text = self._extract_pdf(content)

            elif file_type == "docx":
                content = (
                    service.files()
                    .get_media(fileId=file_id)
                    .execute()
                )
                text = self._extract_docx(content)

            elif file_type == "txt":
                content = (
                    service.files()
                    .get_media(fileId=file_id)
                    .execute()
                )
                text = content.decode("utf-8") if isinstance(content, bytes) else content

        except Exception as e:
            logger.error(f"Text extraction failed for {name} ({file_id}): {e}")
            return None

        if not text or not text.strip():
            logger.warning(f"Empty content extracted from {name}")
            return None

        file_meta["text"] = text.strip()
        file_meta["file_type"] = file_type
        return file_meta

    def _extract_pdf(self, content: bytes) -> str:
        """Extract text from PDF bytes using pypdf."""
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(p for p in pages if p.strip())

    def _extract_docx(self, content: bytes) -> str:
        """Extract text from DOCX bytes."""
        from docx import Document

        doc = Document(io.BytesIO(content))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def _extract_spreadsheet(self, file_id: str, name: str) -> str:
        """Extract spreadsheet as structured text via Sheets API.

        Returns a text representation suitable for the sheet_table chunker.
        """
        sheets_service = self._get_sheets_service()

        # Get all sheet names
        spreadsheet = (
            sheets_service.spreadsheets()
            .get(spreadsheetId=file_id, fields="sheets.properties.title")
            .execute()
        )
        sheet_names = [
            s["properties"]["title"]
            for s in spreadsheet.get("sheets", [])
        ]

        all_text = []
        for sheet_name in sheet_names:
            result = (
                sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=file_id, range=sheet_name)
                .execute()
            )
            values = result.get("values", [])
            if not values:
                continue

            headers = values[0] if values else []
            rows = values[1:] if len(values) > 1 else []

            # Store as structured text for the spreadsheet chunker
            header_str = " | ".join(headers)
            all_text.append(f"Sheet: {sheet_name}\nColumns: {header_str}")
            for row in rows[:100]:  # cap at 100 rows per sheet
                padded = row + [""] * (len(headers) - len(row))
                pairs = [
                    f"{h}: {v}" for h, v in zip(headers, padded) if v.strip()
                ]
                all_text.append("; ".join(pairs))

        return "\n".join(all_text)

    def transform(self, raw_docs: list[dict]) -> list[NormalizedRecord]:
        """Transform raw Drive documents into chunked NormalizedRecords."""
        now_iso = datetime.now(timezone.utc).isoformat()
        all_records: list[NormalizedRecord] = []

        for doc in raw_docs:
            doc_id = f"gdrive:{doc['id']}"
            file_type = doc.get("file_type", "txt")
            text = doc["text"]

            # Choose chunking strategy based on file type
            if file_type == "gsheet":
                # Spreadsheet data — already structured
                chunks = chunk_prose(text, min_tokens=200, max_tokens=400)
            elif self._looks_regulatory(text):
                chunks = chunk_regulatory(text)
            else:
                chunks = chunk_prose(text)

            # Set total_chunks
            for chunk in chunks:
                chunk.total_chunks = len(chunks)

            for chunk in chunks:
                ext_id = f"google_drive:{doc['id']}:chunk:{chunk.chunk_index:04d}"
                records = NormalizedRecord(
                    external_id=ext_id,
                    source_type="google_drive",
                    source_url=doc.get("webViewLink", ""),
                    title=doc["name"],
                    author="Google Drive",
                    published_at=doc.get("modifiedTime", now_iso),
                    fetched_at=now_iso,
                    freshness_class="static",
                    content_kind="doc_section"
                    if file_type != "gsheet"
                    else "sheet_table",
                    text=chunk.text,
                    chunk_index=chunk.chunk_index,
                    total_chunks=chunk.total_chunks,
                    parent_document_id=doc_id,
                    metadata_json=json.dumps(
                        {
                            "drive_file_id": doc["id"],
                            "mime_type": doc["mimeType"],
                            "file_type": file_type,
                        }
                    ),
                )
                all_records.append(records)

        return all_records

    @staticmethod
    def _looks_regulatory(text: str) -> bool:
        """Heuristic: does this text look like a regulatory document?"""
        indicators = [
            "Section ", "SECTION ", "§", "pursuant to",
            "regulation", "compliance", "disclosure",
            "Act of ", "Code of Federal Regulations",
        ]
        score = sum(1 for ind in indicators if ind in text[:2000])
        return score >= 3

    def get_changes_token(self) -> str:
        """Get current changes page token for incremental sync."""
        service = self._get_drive_service()
        resp = service.changes().getStartPageToken().execute()
        return resp["startPageToken"]

    def fetch_changes(
        self,
        page_token: str,
        folder_ids: list[str],
    ) -> tuple[list[dict], str]:
        """Fetch changed files since page_token.

        Returns (changed_file_metas, new_page_token).
        """
        service = self._get_drive_service()
        changed_files = []
        new_token = page_token

        while True:
            resp = (
                service.changes()
                .list(
                    pageToken=page_token,
                    fields="nextPageToken, newStartPageToken, changes(fileId, file(id, name, mimeType, modifiedTime, webViewLink, parents))",
                    spaces="drive",
                )
                .execute()
            )

            for change in resp.get("changes", []):
                f = change.get("file")
                if not f:
                    continue
                # Only include files from our watched folders
                parents = f.get("parents", [])
                if any(p in folder_ids for p in parents):
                    doc = self._extract_text(service, f)
                    if doc:
                        changed_files.append(doc)

            page_token = resp.get("nextPageToken")
            if not page_token:
                new_token = resp.get("newStartPageToken", new_token)
                break

        return changed_files, new_token
