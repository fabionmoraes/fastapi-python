-- TimescaleDB (já presente na imagem timescale/timescaledb)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- PGVector: em algumas imagens Timescale o pacote pode precisar ser instalado no host.
-- Se falhar, use uma imagem com pgvector ou instale o pacote no container.
CREATE EXTENSION IF NOT EXISTS vector;
