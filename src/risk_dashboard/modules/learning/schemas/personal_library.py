"""Validated metadata for private documents and saved catalog references."""

from typing import Literal
from urllib.parse import unquote, urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

DocumentKind = Literal["book", "paper", "document"]
ReadingStatus = Literal["want_to_read", "reading", "completed"]


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=240)
    author: str = Field(default="", max_length=240)
    kind: DocumentKind = "book"


class CatalogDocument(DocumentMetadata):
    source_id: str = Field(default="", max_length=240)
    source_url: str = Field(min_length=1, max_length=2048)
    page_count: int | None = Field(default=None, ge=1, le=10000)
    content_role: Literal["fulltext", "notes", "sample", "reference"] = "fulltext"

    @field_validator("source_url")
    @classmethod
    def safe_source(cls, value):
        parsed = urlsplit(value)
        path = unquote(parsed.path)
        if (
            any(ord(char) < 32 for char in value)
            or "\\" in value
            or parsed.username
            or parsed.password
            or ".." in path.split("/")
            or path.startswith("/api/")
        ):
            raise ValueError("Liên kết tài liệu không hợp lệ.")
        if value.startswith("/"):
            if parsed.netloc or not path.startswith("/learning-assets/books/"):
                raise ValueError("Liên kết tài liệu không hợp lệ.")
        elif parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Liên kết tài liệu không hợp lệ.")
        # A fragment is a reading position, not a different document.
        return parsed._replace(fragment="").geturl()


class LibraryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(default="", min_length=1, max_length=240)
    author: str = Field(default="", max_length=240)
    kind: DocumentKind = "book"
    status: ReadingStatus = "want_to_read"
    current_page: int = Field(default=1, ge=1, le=10000)


class ReadingEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
