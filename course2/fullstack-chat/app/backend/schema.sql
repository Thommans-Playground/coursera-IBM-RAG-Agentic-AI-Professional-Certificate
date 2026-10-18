CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS conversations (
    id          text PRIMARY KEY,
    title       text NOT NULL DEFAULT 'New chat',
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id               bigserial PRIMARY KEY,
    conversation_id  text NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             text NOT NULL CHECK (role IN ('user', 'assistant')),
    content          text NOT NULL,
    sources          jsonb NOT NULL DEFAULT '[]',
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS messages_conv_idx ON messages (conversation_id, id);

-- One row per OWASP category page.
CREATE TABLE IF NOT EXISTS documents (
    id          serial PRIMARY KEY,
    key         text UNIQUE NOT NULL,
    title       text NOT NULL,
    url         text NOT NULL,
    status      text NOT NULL DEFAULT 'queued',
    chunks      int NOT NULL DEFAULT 0,
    error       text NOT NULL DEFAULT '',
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Many rows per document. 1536 is the size of text-embedding-3-small vectors.
CREATE TABLE IF NOT EXISTS chunks (
    id           bigserial PRIMARY KEY,
    document_id  int NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position     int NOT NULL,
    content      text NOT NULL,
    embedding    vector(1536) NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
