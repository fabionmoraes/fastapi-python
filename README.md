# Backend FastAPI (arquitetura limpa)

API em **FastAPI** com **PostgreSQL** (TimescaleDB + PGVector), **Redis**, filas **ARQ**, JWT e métricas **Prometheus**.

## Requisitos

- **Python** 3.12 ou superior (testado com 3.14)
- **Docker** e Docker Compose (para Postgres + Redis)
- Opcional: `openssl` para gerar `SECRET_KEY`

## Configuração rápida

### 1. Ambiente virtual e dependências

```bash
cd fastapi
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

### 2. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` e defina pelo menos:

- `SECRET_KEY`: chave forte (ex.: `openssl rand -hex 32`)
- `DATABASE_URL`: alinhado ao Postgres local (o padrão do `.env.example` combina com o `docker-compose`)

### 3. Banco e Redis (Docker)

```bash
docker compose up -d
```

Aguarde o Postgres ficar saudável (`docker compose ps`).

### 4. Migrations (Alembic)

Com `DATABASE_URL` carregado (via `.env` na raiz ou export no shell):

```bash
python -m alembic upgrade head
```

### 5. Dados de exemplo (opcional)

```bash
python scripts/seed_demo.py
```

Cria usuário `admin@demo.local` / senha `admin12345`, um produto e um cliente de demonstração (se ainda não existirem).

### 6. Subir a API

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentação interativa: [http://localhost:8000/docs](http://localhost:8000/docs)

### 7. Worker de filas (opcional, outro terminal)

Com **Python 3.14**, o comando oficial `python -m arq ...` pode falhar com *“There is no current event loop”* (limitação do ARQ até corrigirem no pacote). Use o entrypoint do projeto:

```bash
python -m app.workers.cli
```

Ou, após `pip install -e .`:

```bash
arq-worker
```

Em versões mais antigas do Python, ainda funciona:

```bash
python -m arq app.infrastructure.messaging.arq_settings.WorkerSettings
```

Processa jobs enfileirados no Redis (ex.: e-mail de boas-vindas após registro).

---

## Endpoints principais

| Método | Caminho | Autenticação | Descrição |
|--------|---------|----------------|-----------|
| GET | `/health` | Não | Health check |
| GET | `/metrics` | Não | Métricas Prometheus (se `METRICS_ENABLED=true`) |
| POST | `{API_PREFIX}/auth/register` | Não | Registro + JWT |
| POST | `{API_PREFIX}/auth/login` | Não | Login + JWT |
| GET | `{API_PREFIX}/users/me` | Bearer | Usuário atual |
| POST | `{API_PREFIX}/users` | Não | Criar usuário (alternativa ao register) |
| GET/POST | `{API_PREFIX}/products` | GET/POST protegidos | Listar / criar produtos |
| GET/POST | `{API_PREFIX}/clients` | Sim | Listar / criar clientes |
| GET | `{API_PREFIX}/products/{id}/embedding` | Sim | Ler embedding salvo (exemplo no `/docs`) |
| POST | `{API_PREFIX}/products/{id}/embedding/generate` | Sim | Gerar embedding via **OpenAI** a partir do produto |
| PUT | `{API_PREFIX}/products/{id}/embedding` | Sim | Salvar embedding manual (vetor 384 dim.) |
| POST | `{API_PREFIX}/products/search/semantic/text` | Sim | Busca semântica por **texto** (OpenAI → vetor) |
| POST | `{API_PREFIX}/products/search/semantic` | Sim | Busca por similaridade com vetor já calculado |

`API_PREFIX` padrão: **`/api/v1`**.

---

## Exemplos com `curl`

Substitua `TOKEN` pelo `access_token` retornado no login ou registro.

### Health

```bash
curl -s http://localhost:8000/health
```

### Registro

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"senha1234","full_name":"Nome"}'
```

### Login

Senha com **no mínimo 8 caracteres** (validação do schema).

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"senha1234"}'
```

### Usuário autenticado

```bash
curl -s http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer TOKEN"
```

### Listar produtos (com JWT)

```bash
curl -s "http://localhost:8000/api/v1/products?limit=10" \
  -H "Authorization: Bearer TOKEN"
```

### Criar produto

```bash
curl -s -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Camiseta",
    "description":"Algodão",
    "sku":"SKU-001",
    "price":"59.90",
    "stock_quantity":100,
    "category":"vestuário"
  }'
```

### Listar clientes

```bash
curl -s "http://localhost:8000/api/v1/clients?limit=10" \
  -H "Authorization: Bearer TOKEN"
```

### Gerar embedding a partir do produto (OpenAI)

**OpenAPI** é o contrato/documentação em `/docs`. **OpenAI** é o serviço que calcula o vetor. Com `OPENAI_API_KEY` no `.env`, após criar o produto:

```bash
curl -s -X POST "http://localhost:8000/api/v1/products/UUID_DO_PRODUTO/embedding/generate" \
  -H "Authorization: Bearer TOKEN"
```

A API monta um texto (nome, descrição, SKU, categoria), chama `text-embedding-3-small` com **384** dimensões e grava em `product_embeddings`. Sem chave, use o **PUT** `.../embedding` com vetor gerado por outra ferramenta.

### Busca semântica por texto (OpenAI)

Com `OPENAI_API_KEY` no `.env`, envie a consulta em linguagem natural (o backend gera o vetor com o mesmo modelo da indexação):

```bash
curl -s -X POST http://localhost:8000/api/v1/products/search/semantic/text \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"notebook para trabalho","limit":5}'
```

### Busca semântica com vetor pronto (384 dimensões)

O corpo deve conter `query_embedding` com **384** floats (mesma dimensão que o PGVector). Útil se você calcula o vetor fora da API. Exemplo com arquivo:

```bash
curl -s -X POST http://localhost:8000/api/v1/products/search/semantic \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d @query.json
```

(`query.json` → `{"query_embedding": [<384 floats...>], "limit": 5}`)

---

## Migrations (Alembic)

Com `DATABASE_URL` apontando para o Postgres (mesmo valor da aplicação) e o banco acessível:

1. **Gerar migration a partir dos modelos SQLAlchemy** (diff automático):

```bash
python -m alembic revision --autogenerate -m "descricao_curta"
```

Revise o arquivo criado em `alembic/versions/` antes de aplicar (autogenerate pode errar em índices, constraints, extensões, hypertables, etc.).

2. **Aplicar migrations:**

```bash
python -m alembic upgrade head
```

3. **Migration vazia** (para escrever SQL/`op.*` manualmente):

```bash
python -m alembic revision -m "descricao_curta"
```

---

## Estrutura do projeto (resumo)

```
app/
├── api/           # rotas, deps, middleware
├── core/          # config, segurança, logging
├── domain/        # entidades, contratos de repositório, serviços
├── infrastructure/  # SQLAlchemy, Redis, ARQ
├── schemas/       # Pydantic
├── workers/       # tarefas ARQ
└── main.py
```

---

## Problemas comuns

- **422 no login/registro:** corpo JSON inválido, e-mail inválido ou senha com menos de 8 caracteres.
- **401 em rotas protegidas:** header `Authorization: Bearer <token>` ausente ou token expirado.
- **Falha ao subir a API:** Redis inacessível (pool ARQ no startup) ou `DATABASE_URL` incorreto.
- **Extensões no Postgres:** a migration cria `timescaledb` e `vector`; a imagem `timescale/timescaledb` já inclui **pgvector** na prática.
- **Worker ARQ / `get_event_loop` no Python 3.14:** use `python -m app.workers.cli` ou `arq-worker` em vez de `python -m arq ...` (ver seção 7).
