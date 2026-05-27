"""Shared response / pagination wrappers."""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data:    T
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items:      List[T]
    total:      int
    page:       int
    page_size:  int
    total_pages: int


class ErrorResponse(BaseModel):
    success: bool = False
    error:   str
    detail:  Optional[str] = None
