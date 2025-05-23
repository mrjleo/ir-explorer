from typing import TYPE_CHECKING

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from models import (
    Corpus,
    CorpusInfo,
    Dataset,
    DatasetInfo,
    Document,
    DocumentInfo,
    DocumentSearchHit,
    Paginated,
    QRel,
    QRelInfo,
    Query,
    QueryInfo,
)
from sqlalchemy import SQLColumnExpression, and_, desc, func, insert, select, text
from sqlalchemy import delete as delete_
from sqlalchemy.exc import IntegrityError, NoResultFound, ProgrammingError
from sqlalchemy.orm import joinedload

from db import provide_transaction
from db.schema import ORMCorpus, ORMDataset, ORMDocument, ORMQRel, ORMQuery

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class DBController(Controller):
    """Controller that handles database related API endpoints."""

    dependencies = {"transaction": Provide(provide_transaction)}

    @get(path="/get_available_languages")
    async def get_available_languages(self, transaction: "AsyncSession") -> list[str]:
        """List all corpus languages supported by the DB engine (for full-text search).

        :return: All available languages.
        """
        sql = text("SELECT cfgname FROM pg_catalog.pg_ts_config;")

        result = (await transaction.execute(sql)).scalars().all()
        return list(result)

    @post(path="/create_corpus")
    async def create_corpus(
        self, transaction: "AsyncSession", data: CorpusInfo
    ) -> None:
        """Create a new corpus in the database.

        :param transaction: A DB transaction.
        :param data: The corpus.
        :raises HTTPException: When the corpus cannot be added to the database.
        """
        sql = insert(ORMCorpus).values({"name": data.name, "language": data.language})

        try:
            await transaction.execute(sql)
        except (IntegrityError, ProgrammingError) as e:
            raise HTTPException(
                "Failed to add corpus.",
                status_code=HTTP_409_CONFLICT,
                extra={"corpus_name": data.name, "error_code": e.code},
            )

    @post(path="/create_dataset")
    async def create_dataset(
        self, transaction: "AsyncSession", data: DatasetInfo
    ) -> None:
        """Create a new dataset in the database.

        :param transaction: A DB transaction.
        :param data: The dataset.
        :raises HTTPException: When the dataset cannot be added to the database.
        """
        sql = insert(ORMDataset).values(
            {
                "name": data.name,
                "corpus_id": select(ORMCorpus.id).filter_by(name=data.corpus_name),
                "min_relevance": data.min_relevance,
            }
        )

        try:
            await transaction.execute(sql)
        except IntegrityError as e:
            raise HTTPException(
                "Failed to add dataset.",
                status_code=HTTP_409_CONFLICT,
                extra={
                    "name": data.name,
                    "corpus_name": data.corpus_name,
                    "error_code": e.code,
                },
            )

    @post(path="/add_queries")
    async def add_queries(
        self,
        transaction: "AsyncSession",
        dataset_name: str,
        corpus_name: str,
        data: "Sequence[QueryInfo]",
    ) -> None:
        """Insert new queries into the database.

        :param transaction: A DB transaction.
        :param dataset_name: The dataset the queries belong to.
        :param corpus_name: The corpus the dataset belongs to.
        :param data: The queries to insert.
        :raises HTTPException: When the queries cannot be added to the database.
        """
        dataset_cte = (
            select(ORMDataset)
            .join(ORMCorpus)
            .where(
                and_(
                    ORMDataset.name == dataset_name,
                    ORMCorpus.name == corpus_name,
                )
            )
        ).cte()
        sql = insert(ORMQuery).values(
            [
                {
                    "id": q.id,
                    "dataset_id": select(dataset_cte.c.id),
                    "text": q.text,
                    "description": q.description,
                }
                for q in data
            ]
        )

        try:
            await transaction.execute(sql)
        except IntegrityError as e:
            raise HTTPException(
                "Failed to add queries.",
                status_code=HTTP_409_CONFLICT,
                extra={"error_code": e.code},
            )

    @post(path="/add_documents")
    async def add_documents(
        self,
        transaction: "AsyncSession",
        corpus_name: str,
        data: "Sequence[DocumentInfo]",
    ) -> None:
        """Insert new documents into the database.

        :param transaction: A DB transaction.
        :param corpus_name: The corpus the documents belong to.
        :param data: The documents to insert.
        :raises HTTPException: When the documents cannot be added to the database.
        """
        corpus_cte = select(ORMCorpus).where(ORMCorpus.name == corpus_name).cte()
        sql = insert(ORMDocument).values(
            [
                {
                    "id": doc.id,
                    "corpus_id": select(corpus_cte.c.id),
                    "title": doc.title,
                    "text": doc.text,
                    "language": select(corpus_cte.c.language),
                }
                for doc in data
            ]
        )

        try:
            await transaction.execute(sql)
        except IntegrityError as e:
            raise HTTPException(
                "Failed to add Documents.",
                status_code=HTTP_409_CONFLICT,
                extra={"error_code": e.code},
            )

    @post(path="/add_qrels")
    async def add_qrels(
        self,
        transaction: "AsyncSession",
        dataset_name: str,
        corpus_name: str,
        data: "Sequence[QRelInfo]",
    ) -> None:
        """Insert QRels into the database.

        :param transaction: A DB transaction.
        :param dataset_name: The dataset the QRels belong to.
        :param corpus_name: The corpus the dataset belongs to.
        :param data: The QRels to insert.
        :raises HTTPException: When the QRels cannot be added to the database.
        """
        dataset_cte = (
            select(ORMDataset)
            .join(ORMCorpus)
            .where(
                and_(
                    ORMDataset.name == dataset_name,
                    ORMCorpus.name == corpus_name,
                )
            )
        ).cte()
        sql = insert(ORMQRel).values(
            [
                {
                    "query_id": qrel.query_id,
                    "document_id": qrel.document_id,
                    "corpus_id": select(dataset_cte.c.corpus_id),
                    "dataset_id": select(dataset_cte.c.id),
                    "relevance": qrel.relevance,
                }
                for qrel in data
            ]
        )

        try:
            await transaction.execute(sql)
        except IntegrityError as e:
            raise HTTPException(
                "Failed to add QRels.",
                status_code=HTTP_409_CONFLICT,
                extra={"error_code": e.code},
            )

    @get(path="/get_corpora")
    async def get_corpora(self, transaction: "AsyncSession") -> list[Corpus]:
        """List all corpora including statistics about datasets and documents.

        :param transaction: A DB transaction.
        :param num_results: How many corpora to return.
        :param offset: Offset for pagination.
        :return: The list of corpora.
        """
        sql = (
            select(
                ORMCorpus,
                func.count(ORMDataset.id),
                func.estimate_num_docs(ORMCorpus.id).label("num_documents_estimate"),
            )
            .join(ORMDataset)
            .group_by(ORMCorpus.id)
        )

        result = (await transaction.execute(sql)).all()
        return [
            Corpus(
                name=corpus.name,
                language=corpus.language,
                num_datasets=num_datasets,
                num_documents_estimate=num_docs,
            )
            for corpus, num_datasets, num_docs in result
        ]

    @get(path="/get_datasets")
    async def get_datasets(
        self, transaction: "AsyncSession", corpus_name: str
    ) -> list[Dataset]:
        """List all datasets for a corpus, including statistics.

        :param transaction: A DB transaction.
        :param corpus_name: The name of the corpus.
        :return: The list of datasets.
        """
        sql = (
            select(
                ORMDataset,
                func.estimate_num_queries(ORMDataset.id).label("num_queries_estimate"),
            )
            .join(ORMCorpus)
            .where(ORMCorpus.name == corpus_name)
        )

        result = (await transaction.execute(sql)).all()
        return [
            Dataset(
                name=dataset.name,
                corpus_name=corpus_name,
                min_relevance=dataset.min_relevance,
                num_queries_estimate=num_queries_estimate,
            )
            for dataset, num_queries_estimate in result
        ]

    @get(path="/get_queries")
    async def get_queries(
        self,
        transaction: "AsyncSession",
        corpus_name: str,
        dataset_name: str | None = None,
        match: str | None = None,
        num_results: int | None = 10,
        offset: int = 0,
    ) -> Paginated[Query]:
        """List queries.

        :param transaction: A DB transaction.
        :param corpus_name: The name of the corpus.
        :param dataset_name: Return only queries in this dataset.
        :param match: Return only queries that match this string.
        :param num_results: How many queries to return.
        :param offset: Offset for pagination.
        :return: Paginated list of queries.
        """
        where_clauses = [ORMCorpus.name == corpus_name]
        if dataset_name is not None:
            where_clauses.append(ORMDataset.name == dataset_name)
        if match is not None:
            where_clauses.append(ORMQuery.text.match(match))

        sql_count = (
            select(func.count(ORMQuery.id))
            .join(ORMDataset)
            .join(ORMCorpus, ORMDataset.corpus_id == ORMCorpus.id)
            .where(*where_clauses)
        )

        sql = (
            select(
                ORMQuery,
                func.count(ORMQRel.relevance >= ORMDataset.min_relevance),
                ORMDataset.name,
            )
            .join(ORMDataset)
            .join(ORMCorpus, ORMDataset.corpus_id == ORMCorpus.id)
            .outerjoin(
                ORMQRel,
                and_(
                    ORMQRel.query_id == ORMQuery.id,
                    ORMQRel.dataset_id == ORMDataset.id,
                    ORMQRel.relevance >= ORMDataset.min_relevance,
                ),
            )
            .where(*where_clauses)
            .group_by(ORMQuery.id, ORMQuery.dataset_id, ORMDataset.name)
            .offset(offset)
        )
        if num_results is not None:
            sql = sql.limit(num_results)

        total_num_results = (await transaction.execute(sql_count)).scalar_one()
        result = (await transaction.execute(sql)).all()
        return Paginated[Query](
            items=[
                Query(
                    id=db_query.id,
                    corpus_name=corpus_name,
                    dataset_name=dataset_name,
                    text=db_query.text,
                    description=db_query.description,
                    num_relevant_documents=num_rel_docs,
                )
                for db_query, num_rel_docs, dataset_name in result
            ],
            offset=offset,
            total_num_items=total_num_results,
        )

    @get(path="/get_query")
    async def get_query(
        self,
        transaction: "AsyncSession",
        corpus_name: str,
        dataset_name: str,
        query_id: str,
    ) -> Query:
        """Return a single specific query.

        :param transaction: A DB transaction.
        :param corpus_name: The name of the corpus.
        :param dataset_name: The dataset name.
        :param query_id: The query ID.
        :raises HTTPException: When the query does not exist.
        :return: The query object.
        """
        sql = (
            select(ORMQuery, func.count(ORMQRel.document_id))
            .join(ORMDataset)
            .join(ORMCorpus, ORMDataset.corpus_id == ORMCorpus.id)
            .outerjoin(
                ORMQRel,
                and_(
                    ORMQRel.query_id == ORMQuery.id,
                    ORMQRel.relevance >= ORMDataset.min_relevance,
                ),
            )
            .where(
                and_(
                    ORMQuery.id == query_id,
                    ORMCorpus.name == corpus_name,
                    ORMDataset.name == dataset_name,
                )
            )
            .group_by(ORMQuery.id, ORMQuery.dataset_id)
        )

        try:
            db_query, num_rel_docs = (await transaction.execute(sql)).one()
        except NoResultFound:
            raise HTTPException(
                "Could not find the requested query.",
                status_code=HTTP_404_NOT_FOUND,
                extra={
                    "query_id": query_id,
                    "dataset_name": dataset_name,
                    "corpus_name": corpus_name,
                },
            )
        return Query(
            id=db_query.id,
            corpus_name=corpus_name,
            dataset_name=dataset_name,
            text=db_query.text,
            description=db_query.description,
            num_relevant_documents=num_rel_docs,
        )

    @get(path="/get_document")
    async def get_document(
        self, transaction: "AsyncSession", corpus_name: str, document_id: str
    ) -> Document:
        """Return a single specific document.

        :param transaction: A DB transaction.
        :param corpus_name: The corpus name.
        :param document_id: The document ID.
        :raises HTTPException: When the document does not exist.
        :return: The document object.
        """
        sql = (
            select(ORMDocument, func.count(ORMQRel.query_id))
            .join(ORMCorpus, ORMDocument.corpus_id == ORMCorpus.id)
            .join(ORMDataset)
            .outerjoin(
                ORMQRel,
                and_(
                    ORMQRel.document_id == ORMDocument.id,
                    ORMQRel.relevance >= ORMDataset.min_relevance,
                ),
            )
            .where(ORMCorpus.name == corpus_name, ORMDocument.id == document_id)
        ).group_by(ORMDocument.id, ORMDocument.corpus_id)

        try:
            db_document, num_rel_queries = (await transaction.execute(sql)).one()
        except NoResultFound as e:
            raise HTTPException(
                "Could not find the requested document.",
                status_code=HTTP_404_NOT_FOUND,
                extra={
                    "document_id": document_id,
                    "corpus_name": corpus_name,
                    "error_code": e.code,
                },
            )
        return Document(
            id=db_document.id,
            title=db_document.title,
            text=db_document.text,
            corpus_name=corpus_name,
            num_relevant_queries=num_rel_queries,
        )

    @get(path="/get_documents")
    async def get_documents(
        self,
        transaction: "AsyncSession",
        corpus_name: str,
        num_results: int | None = 10,
        offset: int = 0,
    ) -> Paginated[Document]:
        """Return all documents in a corpus.

        :param transaction: A DB transaction.
        :param corpus_name: The name of the corpus.
        :param num_results: How many documents to return.
        :param offset: Offset for pagination.
        :return: Paginated list of documents.
        """
        sql_count = (
            select(func.count(ORMDocument.id))
            .join(ORMCorpus)
            .where(ORMCorpus.name == corpus_name)
        )

        sql = (
            select(
                ORMDocument, func.count(ORMQRel.relevance >= ORMDataset.min_relevance)
            )
            .join(ORMCorpus, ORMDocument.corpus_id == ORMCorpus.id)
            .join(ORMDataset)
            .outerjoin(
                ORMQRel,
                and_(
                    ORMQRel.document_id == ORMDocument.id,
                    ORMQRel.dataset_id == ORMDataset.id,
                    ORMQRel.relevance >= ORMDataset.min_relevance,
                ),
            )
            .where(ORMCorpus.name == corpus_name)
            .group_by(ORMDocument.id, ORMDocument.corpus_id)
            .offset(offset)
        )
        if num_results is not None:
            sql = sql.limit(num_results)

        total_num_results = (await transaction.execute(sql_count)).scalar_one()
        result = (await transaction.execute(sql)).all()
        return Paginated[Document](
            items=[
                Document(
                    id=db_document.id,
                    corpus_name=corpus_name,
                    title=db_document.title,
                    text=db_document.text,
                    num_relevant_queries=num_rel_queries,
                )
                for db_document, num_rel_queries in result
            ],
            offset=offset,
            total_num_items=total_num_results,
        )

    @get(path="/search_documents")
    async def search_documents(
        self,
        transaction: "AsyncSession",
        q: str,
        language: str = "english",
        corpus_name: list[str] | None = None,
        num_results: int | None = 10,
        offset: int = 0,
    ) -> Paginated[DocumentSearchHit]:
        """Search documents (using full-text search).

        :param transaction: A DB transaction.
        :param q: The search query.
        :param language: The query language.
        :param corpus_name: Search only within these corpora.
        :param num_results: How many hits to return.
        :param offset: Offset for pagination.
        :return: Paginated list of results, ordered by score.
        """
        ts_query = func.websearch_to_tsquery(language, q)

        where_clauses: list[SQLColumnExpression] = [
            ORMDocument.text_tsv.bool_op("@@")(ts_query)
        ]
        if corpus_name is not None:
            where_clauses.append(ORMCorpus.name.in_(corpus_name))

        # count the total number of hits
        sql_count = (
            select(func.count(ORMDocument.id))
            .join(ORMCorpus)
            .where(
                and_(*where_clauses),
            )
        )

        # score and rank documents, select a subset to return
        ts_rank = func.ts_rank_cd(ORMDocument.text_tsv, ts_query)

        # results for the current page only
        sql_results_page = (
            select(
                ORMDocument.id.label("id"),
                ORMDocument.title.label("title"),
                ORMDocument.text.label("text"),
                ORMCorpus.name.label("corpus_name"),
                ts_rank.label("score"),
            )
            .join(ORMCorpus)
            .where(
                and_(*where_clauses),
            )
            .order_by(desc("score"))
            .order_by(ORMDocument.id)
            .offset(offset)
        )
        if num_results is not None:
            sql_results_page = sql_results_page.limit(num_results)

        # compute snippets for the current page
        sql_results = select(
            text("id"),
            text("title"),
            text("corpus_name"),
            text("score"),
            func.ts_headline(
                text("text"),
                ts_query,
                "MaxFragments=5, FragmentDelimiter=' [...] '",
            ).label("snippet"),
        ).select_from(sql_results_page.subquery())

        total_num_results = (await transaction.execute(sql_count)).scalar_one()
        results = (await transaction.execute(sql_results)).all()
        return Paginated[DocumentSearchHit](
            items=[
                DocumentSearchHit(
                    id=id,
                    corpus_name=corpus_name,
                    title=title,
                    snippet=snippet,
                    score=score,
                )
                for id, title, corpus_name, score, snippet in results
            ],
            offset=offset,
            total_num_items=total_num_results,
        )

    @get(path="/get_qrels")
    async def get_qrels(
        self,
        transaction: "AsyncSession",
        corpus_name: str,
        document_id: str | None = None,
        dataset_name: str | None = None,
        query_id: str | None = None,
        num_results: int | None = 10,
        offset: int = 0,
    ) -> Paginated[QRel]:
        """Return query-document pairs annotated as relevant.

        :param transaction: A DB transaction.
        :param corpus_name: The corpus name.
        :param document_id: Return QRels for this document only.
        :param dataset_name: Return QRels for this dataset only.
        :param query_id: Return QRels for this query only.
        :param num_results: How many QRels to return.
        :param offset: Offset for pagination.
        :return: Paginated list of QRels, ordered by relevance.
        """
        where_clauses = [
            ORMCorpus.name == corpus_name,
            ORMQRel.relevance >= ORMDataset.min_relevance,
        ]
        if document_id is not None:
            where_clauses.append(ORMQRel.document_id == document_id)
        if dataset_name is not None:
            where_clauses.append(ORMDataset.name == dataset_name)
        if query_id is not None:
            where_clauses.append(ORMQRel.query_id == query_id)

        sql_count = (
            select(func.count())
            .select_from(ORMQRel)
            .join(ORMDataset, ORMQRel.dataset_id == ORMDataset.id)
            .join(ORMCorpus)
            .where(and_(*where_clauses))
        )

        sql = (
            select(ORMQRel)
            .join(ORMDataset, ORMQRel.dataset_id == ORMDataset.id)
            .join(ORMCorpus)
            .options(
                joinedload(ORMQRel.document).joinedload(ORMDocument.corpus),
                joinedload(ORMQRel.query)
                .joinedload(ORMQuery.dataset)
                .joinedload(ORMDataset.corpus),
            )
            .where(and_(*where_clauses))
            .order_by(ORMQRel.relevance.desc())
            .offset(offset)
        )
        if num_results is not None:
            sql = sql.limit(num_results)

        total_num_results = (await transaction.execute(sql_count)).scalar_one()
        result = (await transaction.execute(sql)).scalars()
        return Paginated[QRel](
            items=[
                QRel(
                    query_info=QueryInfo(
                        id=qrel.query.id,
                        text=qrel.query.text,
                        description=qrel.query.description,
                    ),
                    document_info=DocumentInfo(
                        id=qrel.document.id,
                        title=qrel.document.title,
                        text=qrel.document.text,
                    ),
                    relevance=qrel.relevance,
                    corpus_name=qrel.document.corpus.name,
                    dataset_name=qrel.query.dataset.name,
                )
                for qrel in result
            ],
            offset=offset,
            total_num_items=total_num_results,
        )

    @delete(path="/remove_dataset")
    async def remove_dataset(
        self, transaction: "AsyncSession", corpus_name: str, dataset_name: str
    ) -> None:
        """Remove a dataset and its associated queries and QRels.

        :param transaction: A DB transaction.
        :param corpus_name: The name of the corpus the dataset is in.
        :param dataset_name: The name of the dataset to remove.
        """
        dataset_id = (
            select(ORMDataset.id)
            .join(ORMCorpus)
            .where(and_(ORMDataset.name == dataset_name, ORMCorpus.name == corpus_name))
        ).scalar_subquery()
        sql_del_qrels = delete_(ORMQRel).filter_by(dataset_id=dataset_id)
        sql_del_queries = delete_(ORMQuery).filter_by(dataset_id=dataset_id)
        sql_del_dataset = delete_(ORMDataset).filter_by(id=dataset_id)

        await transaction.execute(sql_del_qrels)
        await transaction.execute(sql_del_queries)
        await transaction.execute(sql_del_dataset)

    @delete(path="/remove_corpus")
    async def remove_corpus(
        self, transaction: "AsyncSession", corpus_name: str
    ) -> None:
        """Remove a corpus and its associated documents.

        Any associated datasets must be removed first.

        :param transaction: A DB transaction.
        :param corpus_name: The name of the corpus to remove.
        :raises HTTPException: When the corpus still has associated datasets.
        :raises HTTPException: When the corpus cannot be removed for other reasons.
        """
        sql_corpus = (
            select(ORMCorpus)
            .options(joinedload(ORMCorpus.datasets))
            .filter_by(name=corpus_name)
        )
        corpus = (await transaction.execute(sql_corpus)).unique().scalar_one()
        if len(corpus.datasets) > 0:
            raise HTTPException(
                "Associated datasets must be removed first.",
                status_code=HTTP_409_CONFLICT,
                extra={"corpus_name": corpus_name},
            )

        sql_del_documents = delete_(ORMDocument).filter_by(corpus_id=corpus.id)
        sql_del_corpus = delete_(ORMCorpus).filter_by(id=corpus.id)

        try:
            await transaction.execute(sql_del_documents)
            await transaction.execute(sql_del_corpus)
        except IntegrityError as e:
            raise HTTPException(
                "Failed to remove corpus.",
                status_code=HTTP_409_CONFLICT,
                extra={"corpus_name": corpus_name, "error_code": e.code},
            )
