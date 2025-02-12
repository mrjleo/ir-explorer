from dataclasses import dataclass


@dataclass
class Dataset:
    """A dataset."""

    name: str
    corpus_name: str


@dataclass
class BulkQRel:
    """A single query-document relevance score for bulk insertion."""

    query_id: str
    document_id: str
    relevance: int


@dataclass
class QRel(BulkQRel):
    """A single query-document relevance score."""

    corpus_name: str
    dataset_name: str


@dataclass
class BulkQuery:
    """A single query for bulk insertion."""

    id: str
    text: str
    description: str | None


@dataclass
class Query(BulkQuery):
    """A single query."""

    corpus_name: str
    dataset_name: str


@dataclass
class QueryWithRelevanceInfo(Query):
    """A single query with relevance information attached."""

    num_relevant_documents: int


@dataclass
class BulkDocument:
    """A single document for bulk insertion."""

    id: str
    title: str | None
    text: str


@dataclass
class Document(BulkDocument):
    """A single document."""

    corpus_name: str


@dataclass
class DocumentWithRelevance(Document):
    """A single document with a relevance (w.r.t. a specific query)."""

    query_id: str
    relevance: int


@dataclass
class DocumentSearchHit(Document):
    """A document retrieved by a search engine."""

    score: float
