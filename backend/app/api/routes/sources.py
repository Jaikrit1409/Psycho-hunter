import hashlib
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.client import Client
from app.models.document import Document
from app.models.source import Source
from app.schemas.document import DocumentIngestRead
from app.schemas.source import SourceCreate, SourceRead

router = APIRouter(tags=["sources"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_published_at(soup: BeautifulSoup) -> datetime | None:
    candidates = [
        "meta[property='article:published_time']",
        "meta[property='og:article:published_time']",
        "meta[name='pubdate']",
        "meta[name='publishdate']",
        "meta[name='date']",
        "time[datetime]",
        "article time",
    ]

    for selector in candidates:
        element = soup.select_one(selector)
        if not element:
            continue
        candidate = element.get("content") or element.get("datetime") or element.get_text(" ", strip=True)
        if not candidate:
            continue
        candidate = candidate.strip()
        try:
            if candidate.endswith("Z"):
                return datetime.fromisoformat(candidate.replace("Z", "+00:00")).astimezone(timezone.utc)
            return datetime.fromisoformat(candidate).astimezone(timezone.utc)
        except ValueError:
            continue

    return None


def _extract_document_title(soup: BeautifulSoup, fallback_title: str | None) -> str:
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    if title:
        return title
    return fallback_title or "Untitled Document"


def _extract_readable_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "header", "footer", "aside"]):
        tag.decompose()

    article = soup.select_one("main, article")
    if article is not None:
        text = article.get_text(" ", strip=True)
    else:
        text = soup.get_text(" ", strip=True)

    return _normalize_whitespace(text)


@router.post("/clients/{client_id}/sources", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source_for_client(
    client_id: int,
    source_data: SourceCreate,
    db: Session = Depends(get_db),
) -> Source:
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    source = Source(
        client_id=client_id,
        url=str(source_data.url),
        source_type=source_data.source_type,
        title=source_data.title,
        publisher=source_data.publisher,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/clients/{client_id}/sources", response_model=list[SourceRead])
def list_sources_for_client(client_id: int, db: Session = Depends(get_db)) -> list[Source]:
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    return db.query(Source).filter(Source.client_id == client_id).order_by(Source.id).all()


@router.get("/sources/{source_id}", response_model=SourceRead)
def get_source(source_id: int, db: Session = Depends(get_db)) -> Source:
    source = db.query(Source).filter(Source.id == source_id).first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: int, db: Session = Depends(get_db)) -> None:
    source = db.query(Source).filter(Source.id == source_id).first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    db.delete(source)
    db.commit()
    return None


@router.post("/sources/{source_id}/ingest", response_model=DocumentIngestRead, status_code=status.HTTP_201_CREATED)
def ingest_source(source_id: int, db: Session = Depends(get_db)) -> DocumentIngestRead:
    source = db.query(Source).filter(Source.id == source_id).first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    try:
        response = requests.get(source.url, timeout=20, allow_redirects=True)
        response.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to retrieve source URL") from exc

    content_type = (response.headers.get("Content-Type") or "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported response type")

    soup = BeautifulSoup(response.text, "html.parser")
    extracted_content = _extract_readable_text(soup)
    if not extracted_content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No readable content extracted")

    title = _extract_document_title(soup, source.title)
    published_at = _extract_published_at(soup)
    content_hash = hashlib.sha256(extracted_content.encode("utf-8")).hexdigest()
    collected_at = datetime.now(timezone.utc)

    document = Document(
        source_id=source_id,
        title=title,
        content=extracted_content,
        url=str(source.url),
    )
    document.published_at = published_at
    document.collected_at = collected_at
    document.content_hash = content_hash

    db.add(document)
    db.commit()
    db.refresh(document)

    return DocumentIngestRead(
        id=document.id,
        source_id=document.source_id,
        title=document.title,
        content=document.content,
        published_at=published_at,
        collected_at=collected_at,
        content_hash=content_hash,
    )
