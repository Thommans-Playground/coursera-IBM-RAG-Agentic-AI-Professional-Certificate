CREATE EXTENSION IF NOT EXISTS vector;

-- The settings the current index was built with. At most one row.
CREATE TABLE IF NOT EXISTS lab_settings (
    id             int PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    splitter       text NOT NULL,
    chunk_size     int NOT NULL,
    chunk_overlap  int NOT NULL
);

-- One row per chunk. 1536 is the size of text-embedding-3-small vectors.
CREATE TABLE IF NOT EXISTS lab_chunks (
    id         int PRIMARY KEY,
    content    text NOT NULL,
    embedding  vector(1536) NOT NULL
);
CREATE INDEX IF NOT EXISTS lab_chunks_embedding_idx ON lab_chunks USING hnsw (embedding vector_cosine_ops);
