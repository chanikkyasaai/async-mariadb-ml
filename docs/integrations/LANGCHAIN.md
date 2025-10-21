# LangChain Integration Guide for async-mariadb-connector

This guide shows how to use **async-mariadb-connector** with **LangChain** for building powerful database applications with natural language interfaces.

## Overview

LangChain is a popular framework for building applications with Large Language Models (LLMs). This integration allows you to:

- 🤖 **Natural Language SQL** - Convert questions to SQL queries
- 📚 **RAG with MariaDB** - Use MariaDB as a vector store for retrieval-augmented generation
- 🔄 **Async Operations** - Leverage async/await for better performance
- 🔗 **Hybrid Search** - Combine full-text and semantic search

## Prerequisites

```bash
# Install the connector from PyPI
pip install async-mariadb-connector

# Install LangChain (optional - for LLM integration)
pip install langchain langchain-openai
```

## Quick Start with Docker

Use the provided docker-compose setup for a local MariaDB instance:

```bash
# Start MariaDB with sample data
docker-compose up -d

# Verify it's running
docker-compose ps
```

This creates a MariaDB 11.8.3 instance with:
- Sample `users`, `products`, and `embeddings` tables
- UTF-8 support (utf8mb4)
- JSON data type support
- Full-text search indexes

## Example 1: SQL Chain (Natural Language → SQL)

```python
import asyncio
from async_mariadb_connector import AsyncMariaDB

async def main():
    db = AsyncMariaDB()
    
    # Get database schema
    schema = await db.fetch_all("""
        SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
    """)
    
    # In production, use an LLM to convert natural language to SQL
    # For example: "Show me all users older than 30"
    # LLM generates: SELECT * FROM users WHERE age > 30
    
    natural_query = "Show me all users older than 30"
    sql_query = "SELECT name, email, age FROM users WHERE age > 30"
    
    results = await db.fetch_all(sql_query)
    
    for user in results:
        print(f"{user['name']}: {user['age']} years old")
    
    await db.close()

asyncio.run(main())
```

## Example 2: Vector Store for RAG

Use MariaDB to store document embeddings for semantic search:

```python
import asyncio
import json
import numpy as np
from async_mariadb_connector import AsyncMariaDB

async def setup_vector_store():
    db = AsyncMariaDB()
    
    # Create table for embeddings
    await db.execute("""
        CREATE TABLE IF NOT EXISTS document_embeddings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            content TEXT NOT NULL,
            embedding JSON NOT NULL,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FULLTEXT INDEX ft_content (content)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    await db.close()

async def add_documents(documents, embeddings):
    db = AsyncMariaDB()
    
    insert_sql = """
        INSERT INTO document_embeddings (content, embedding, metadata)
        VALUES (%s, %s, %s)
    """
    
    data = [
        (doc, json.dumps(emb), json.dumps({"source": "manual"}))
        for doc, emb in zip(documents, embeddings)
    ]
    
    await db.execute_many(insert_sql, data)
    await db.close()

async def similarity_search(query_embedding, k=5):
    db = AsyncMariaDB()
    
    # Fetch all embeddings (optimize with pagination for large datasets)
    results = await db.fetch_all(
        "SELECT id, content, embedding FROM document_embeddings"
    )
    
    # Calculate cosine similarity
    query_vec = np.array(query_embedding)
    similarities = []
    
    for row in results:
        doc_vec = np.array(json.loads(row['embedding']))
        similarity = np.dot(query_vec, doc_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
        )
        similarities.append((row['content'], similarity))
    
    # Return top k
    similarities.sort(key=lambda x: x[1], reverse=True)
    await db.close()
    
    return similarities[:k]

# Usage
asyncio.run(setup_vector_store())
```

## Example 3: Hybrid Search (Full-Text + Vector)

Combine MariaDB's full-text search with semantic similarity:

```python
async def hybrid_search(query_text, query_embedding, k=5):
    db = AsyncMariaDB()
    
    # Full-text search
    fts_results = await db.fetch_all("""
        SELECT content, 
               MATCH(content) AGAINST(%s IN NATURAL LANGUAGE MODE) as score
        FROM document_embeddings
        WHERE MATCH(content) AGAINST(%s IN NATURAL LANGUAGE MODE)
    """, (query_text, query_text))
    
    # Vector search (as shown above)
    vector_results = await similarity_search(query_embedding, k=k*2)
    
    # Combine and re-rank
    # ... (implement your ranking logic)
    
    await db.close()
    return combined_results
```

## Integration with LangChain Components

### SQL Database Chain

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from async_mariadb_connector import AsyncMariaDB

async def langchain_sql_chain():
    # Setup
    db = AsyncMariaDB()
    llm = ChatOpenAI(model="gpt-4")
    
    # Get schema
    schema = await db.fetch_all("SHOW TABLES")
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a SQL expert. Write queries for MariaDB."),
        ("user", "Schema: {schema}\n\nQuestion: {question}")
    ])
    
    # Chain: prompt → LLM → SQL execution
    question = "How many users are verified?"
    
    # Get SQL from LLM
    response = await llm.ainvoke(
        prompt.format(schema=schema, question=question)
    )
    sql = response.content
    
    # Execute
    results = await db.fetch_all(sql)
    
    await db.close()
    return results
```

### Custom Vector Store

For advanced LangChain integration, implement the `VectorStore` interface:

```python
from langchain_core.vectorstores import VectorStore
from async_mariadb_connector import AsyncMariaDB

class MariaDBVectorStore(VectorStore):
    def __init__(self):
        self.db = AsyncMariaDB()
    
    async def aadd_texts(self, texts, embeddings, metadatas=None):
        # Implementation from Example 2
        pass
    
    async def asimilarity_search(self, query, k=4):
        # Implementation from Example 2
        pass
    
    # ... implement other required methods
```

## Production Tips

### 1. Connection Pooling

```python
# Reuse database connections
class DatabasePool:
    def __init__(self):
        self._db = None
    
    async def get_db(self):
        if self._db is None:
            self._db = AsyncMariaDB()
        return self._db

pool = DatabasePool()
db = await pool.get_db()
```

### 2. Error Handling

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def robust_query(sql):
    db = AsyncMariaDB()
    try:
        return await db.fetch_all(sql)
    finally:
        await db.close()
```

### 3. Batch Operations

```python
# Insert multiple documents efficiently
async def batch_insert(documents, embeddings, batch_size=100):
    db = AsyncMariaDB()
    
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_embs = embeddings[i:i+batch_size]
        
        data = [
            (doc, json.dumps(emb))
            for doc, emb in zip(batch_docs, batch_embs)
        ]
        
        await db.execute_many(
            "INSERT INTO document_embeddings (content, embedding) VALUES (%s, %s)",
            data
        )
    
    await db.close()
```

## Running the Examples

We provide complete working examples in the `examples/integrations/` directory:

1. **SQL Chain Example** - `langchain_mariadb_async.py`
   ```bash
   python examples/integrations/langchain_mariadb_async.py
   ```

2. **RAG Example** - `langchain_mariadb_rag.ipynb`
   ```bash
   jupyter notebook examples/integrations/langchain_mariadb_rag.ipynb
   ```

## Architecture Diagram

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       v
┌─────────────────────────┐
│   LangChain Components  │
│  - Prompt Templates     │
│  - LLM (GPT-4, etc.)   │
│  - Output Parsers       │
└──────┬──────────────────┘
       │
       v
┌───────────────────────────┐
│  async-mariadb-connector  │
│  - AsyncMariaDB class     │
│  - Connection pooling     │
│  - Retry logic            │
└──────┬────────────────────┘
       │
       v
┌─────────────────────┐
│   MariaDB 11.8.3+   │
│  - JSON support     │
│  - Full-text search │
│  - ACID transactions│
└─────────────────────┘
```

## Use Cases

### 1. Chatbot with Database Knowledge
Build a chatbot that answers questions about your database:
- User: "How many products do we have in stock?"
- LLM → SQL: `SELECT COUNT(*) FROM products WHERE stock > 0`
- Execute and return natural language response

### 2. Semantic Document Search
Store and search documents using embeddings:
- Index documentation, support tickets, or knowledge base
- Find relevant content using semantic similarity
- Combine with full-text search for hybrid retrieval

### 3. Data Analysis Assistant
Let users analyze data with natural language:
- "What's the average order value this month?"
- "Show me top customers by revenue"
- Generate visualizations from query results

## Resources

- **Package**: [async-mariadb-connector on PyPI](https://pypi.org/project/async-mariadb-connector/)
- **Examples**: See `examples/integrations/` directory
- **MariaDB Guide**: See `docs/MARIADB_NOTES.md` for best practices
- **LangChain Docs**: [LangChain SQL Database](https://python.langchain.com/docs/integrations/sql_databases/)

## Need Help?

- 🐛 Issues: [GitHub Issues](https://github.com/chanikkyasaai/async-mariadb-ml/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/chanikkyasaai/async-mariadb-ml/discussions)
- 📖 Docs: See `README.md` and `docs/` directory

## Contributing

We welcome contributions! If you've built something cool with this integration:

1. Share your example in `examples/integrations/`
2. Update this guide with your use case
3. Submit a PR

See `CONTRIBUTING.md` for guidelines.

---

**Built with ❤️ for the MariaDB Python Hackathon**
