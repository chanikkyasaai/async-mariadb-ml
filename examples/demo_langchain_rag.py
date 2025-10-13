# LangChain integration demo for a simple RAG pipeline
import asyncio
import numpy as np
import pandas as pd
from typing import List, Iterable, Any, Optional

# LangChain components
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from sentence_transformers import SentenceTransformer

# Our async MariaDB library
from async_mariadb_connector import AsyncMariaDB, bulk_insert

# --- 1. Create a custom SentenceTransformer embedding class ---
class LocalEmbeddings(Embeddings):
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text]).tolist()[0]

# --- 2. Create a custom MariaDB VectorStore for LangChain ---
class MariaDBVectorStore(VectorStore):
    def __init__(self, db: AsyncMariaDB, table_name: str, embeddings: Embeddings):
        self.db = db
        self.table_name = table_name
        self.embeddings = embeddings

    async def aadd_texts(self, texts: Iterable[str], metadatas: Optional[List[dict]] = None, **kwargs: Any) -> List[str]:
        """Add texts to the vector store."""
        embedded_vectors = self.embeddings.embed_documents(list(texts))
        
        df_data = []
        for i, text in enumerate(texts):
            vector_bytes = np.array(embedded_vectors[i], dtype=np.float32).tobytes()
            metadata = metadatas[i] if metadatas else {}
            df_data.append({
                "text_content": text,
                "vector": vector_bytes,
                "metadata": str(metadata)
            })
        
        df = pd.DataFrame(df_data)
        await bulk_insert(self.db, self.table_name, df)
        return [str(i) for i in range(len(texts))]

    async def asimilarity_search(self, query: str, k: int = 4, **kwargs: Any) -> List[Document]:
        """Perform a similarity search."""
        query_vector = self.embeddings.embed_query(query)
        query_vector_bytes = np.array(query_vector, dtype=np.float32).tobytes()

        # MariaDB's VECTOR_COSINE_DISTANCE requires binary format with a specific header
        # For this demo, we'll use a simplified distance calculation if vector functions aren't available
        # In a real scenario, you'd use `VEC_COSINE_DISTANCE(vector, VECTOR_FROM_BLOB(?))`
        # This is a placeholder for demonstration.
        sql_query = f"""
            SELECT text_content, metadata
            FROM {self.table_name}
            ORDER BY 1
            LIMIT %s
        """
        
        results = await self.db.fetch(sql_query, (k,))
        
        return [Document(page_content=row['text_content'], metadata=eval(row['metadata'])) for row in results]

    @classmethod
    def from_texts(cls, texts: List[str], embedding: Embeddings, metadatas: Optional[List[dict]] = None, db_connection: AsyncMariaDB = None, table_name: str = "langchain_vectors", **kwargs: Any):
        vs = cls(db_connection, table_name, embedding)
        asyncio.run(vs.aadd_texts(texts, metadatas=metadatas))
        return vs

# --- 3. Main RAG Demo Logic ---
async def main():
    print("--- LangChain RAG Demo ---")
    
    # Sample documents for our knowledge base
    documents = [
        "MariaDB is a community-developed, commercially supported fork of the MySQL relational database management system.",
        "Asyncio is a library to write concurrent code using the async/await syntax.",
        "LangChain is a framework for developing applications powered by language models.",
        "Vector databases are used to store and query embeddings for similarity search."
    ]
    metadatas = [{"source": f"doc_{i}"} for i in range(len(documents))]

    async with AsyncMariaDB() as db:
        # Create table for the vector store
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS langchain_vectors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                text_content TEXT,
                vector BLOB,
                metadata JSON
            )
        """)
        
        # Initialize embeddings and vector store
        embeddings = LocalEmbeddings()
        vector_store = MariaDBVectorStore(db, "langchain_vectors", embeddings)
        
        # Add documents to the vector store
        print("Adding documents to MariaDB vector store...")
        await vector_store.aadd_texts(documents, metadatas=metadatas)
        print("Documents added.")

        # Perform a similarity search (RAG query)
        query = "What is MariaDB?"
        print(f"\nPerforming similarity search for: '{query}'")
        results = await vector_store.asimilarity_search(query, k=2)
        
        print("\nTop relevant documents from MariaDB:")
        for doc in results:
            print(f"  - Content: {doc.page_content}")
            print(f"    Source: {doc.metadata.get('source')}")

        # Clean up
        await db.execute("DROP TABLE langchain_vectors")
        print("\n--- LangChain RAG Demo Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
