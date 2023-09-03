--
-- depends:

CREATE TABLE quotes (
    id SERIAL PRIMARY KEY,
    quote TEXT NOT NULL,
    author TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
