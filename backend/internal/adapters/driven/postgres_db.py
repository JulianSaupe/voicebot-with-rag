import os
from typing import List

import numpy as np
import psycopg2
from dotenv import load_dotenv

from backend.internal.ports.output.embedding_calculator import EmbeddingCalculator
from backend.internal.ports.output.vector_database import VectorDatabase


class PostgresVectorDB(VectorDatabase):
    def __init__(self, embedding_calculator: EmbeddingCalculator, min_similarity: float = 0.5):
        super().__init__(embedding_calculator, min_similarity)

        load_dotenv()

        self.conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT')
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self) -> None:
        self.cursor.execute("""
                            CREATE EXTENSION IF NOT EXISTS vector;
                            CREATE TABLE IF NOT EXISTS documents
                            (
                                id        SERIAL PRIMARY KEY,
                                content   TEXT,
                                embedding VECTOR(768)
                            );
                            """)

    def insert_document(self, text: str) -> None:
        """
        Inserts or updates a document with its embedding.
        """
        embeddings = self.embedding_calculator.calculate_embeddings(text)
        embedding_str = ','.join(map(str, embeddings))
        self.cursor.execute("""
                            INSERT INTO documents (content, embedding)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING;
                            """, (text, f'[{embedding_str}]'))

    def search(self, query: np.ndarray, top_k: int = 10) -> List[str]:
        """
        Retrieves top-k documents most similar to the query vector.
        """
        embedding_str = ','.join(map(str, query))

        self.cursor.execute(f"""
            SELECT content, embedding <-> %s AS similarity
            FROM documents
            WHERE embedding <-> %s >= %s
            ORDER BY embedding <-> %s
            LIMIT %s;
        """, (f'[{embedding_str}]', f'[{embedding_str}]', self.min_similarity, f'[{embedding_str}]', top_k))

        results = self.cursor.fetchall()
        texts = []

        for text, _ in results:
            texts.append(text)

        return texts
