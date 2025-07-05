import os
import pathlib
import psycopg2
from dotenv import load_dotenv
from app.rag.embedding_calculator import EmbeddingCalculator
from app.rag.vector_database import VectorDatabase


class PostgresVectorDB(VectorDatabase):
    def __init__(self, embedding_calculator: EmbeddingCalculator):
        super().__init__(embedding_calculator)

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

    def create_table(self):
        self.cursor.execute("""
                            CREATE EXTENSION IF NOT EXISTS vector;
                            CREATE TABLE IF NOT EXISTS documents
                            (
                                id        TEXT PRIMARY KEY,
                                content   TEXT,
                                embedding VECTOR(384)
                            );
                            """)

    def insert_document(self, doc_id: str, text: str):
        """
        Inserts or updates a document with its embedding.
        """
        embedding = self.embedding_calculator.calculate_embeddings(text)
        embedding_str = ','.join(map(str, embedding.tolist()))
        self.cursor.execute("""
                            INSERT INTO documents (id, content, embedding)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (id) DO NOTHING;
                            """, (doc_id, text, f'[{embedding_str}]'))

    def search(self, query: str, top_k: int = 10):
        """
        Retrieves top-k documents most similar to the query vector.
        """
        query_embedding = self.embedding_calculator.calculate_embeddings(query)
        embedding_str = ','.join(map(str, query_embedding.tolist()))

        self.cursor.execute(f"""
            SELECT id, content, embedding <=> %s AS similarity
            FROM documents
            ORDER BY embedding <=> %s
            LIMIT %s;
        """, (f'[{embedding_str}]', f'[{embedding_str}]', top_k))

        return self.cursor.fetchall()
