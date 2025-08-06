import os
from typing import List
from functools import lru_cache
import hashlib

import numpy as np
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

from backend.internal.ports.output.embedding_calculator import EmbeddingCalculator
from backend.internal.ports.output.vector_database import VectorDatabase


class PostgresVectorDB(VectorDatabase):
    _connection_pool = None

    def __init__(self, embedding_calculator: EmbeddingCalculator, min_similarity: float = 0.5):
        super().__init__(embedding_calculator, min_similarity)
        load_dotenv()

        # Initialize connection pool (singleton pattern)
        if PostgresVectorDB._connection_pool is None:
            print("🗄️ Creating PostgreSQL connection pool...")
            PostgresVectorDB._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=15,
                dbname=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT')
            )
            print("✅ Connection pool created successfully")
            self.create_table()

    @staticmethod
    def _get_connection():
        """Get connection from pool"""
        return PostgresVectorDB._connection_pool.getconn()

    @staticmethod
    def _put_connection(conn):
        """Return connection to pool"""
        PostgresVectorDB._connection_pool.putconn(conn)

    def create_table(self) -> None:
        """Create a table to store documents."""
        conn = self._get_connection()
        try:
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE EXTENSION IF NOT EXISTS vector;
                           CREATE TABLE IF NOT EXISTS documents
                           (
                               id        SERIAL PRIMARY KEY,
                               content   TEXT,
                               embedding VECTOR(768)
                           );
                           """)
            cursor.close()
        finally:
            self._put_connection(conn)

    def insert_document(self, text: str) -> None:
        """
        Inserts or updates a document with its embedding using connection pool.
        """
        embeddings = self.embedding_calculator.calculate_embeddings(text)
        embedding_str = ','.join(map(str, embeddings))

        conn = self._get_connection()
        try:
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("""
                           INSERT INTO documents (content, embedding)
                           VALUES (%s, %s)
                           ON CONFLICT DO NOTHING;
                           """, (text, f'[{embedding_str}]'))
            cursor.close()
        finally:
            self._put_connection(conn)

    @lru_cache(maxsize=64)
    def _search_cached(self, query_hash: str, query_str: str, top_k: int) -> tuple:
        """
        Cached search implementation to avoid repeated database queries.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT content, embedding <-> %s AS similarity
                           FROM documents
                           WHERE embedding <-> %s >= %s
                           ORDER BY embedding <-> %s
                           LIMIT %s;
                           """, (query_str, query_str, self.min_similarity, query_str, top_k))

            results = cursor.fetchall()
            cursor.close()
            return tuple(text for text, _ in results)
        finally:
            self._put_connection(conn)

    def search(self, query: np.ndarray, top_k: int = 10) -> List[str]:
        """
        Retrieves top-k documents most similar to the query vector with caching.
        """
        embedding_str = ','.join(map(str, query))
        query_str = f'[{embedding_str}]'

        # Create hash for caching
        query_hash = hashlib.md5(f"{query_str}_{top_k}_{self.min_similarity}".encode()).hexdigest()

        # Use cached search
        cached_results = self._search_cached(query_hash, query_str, top_k)
        return list(cached_results)
