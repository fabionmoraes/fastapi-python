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
| PUT | `{API_PREFIX}/products/{id}/embedding` | Sim | Salvar embedding (vetor 384 dim.) |
| POST | `{API_PREFIX}/products/search/semantic` | Sim | Busca por similaridade de vetores |

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

### Busca semântica (exige vetor 384 dimensões)

O corpo deve conter `query_embedding` com **384** floats (mesma dimensão configurada em `app/core/constants.py` e usada em `PUT .../products/{id}/embedding`). Gere o vetor com o mesmo modelo que indexar os produtos. Envie o JSON via arquivo para não digitar o vetor no terminal:

```bash
# query.json → {"query_embedding": [<384 floats...>], "limit": 5}
curl -s -X POST http://localhost:8000/api/v1/products/search/semantic \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d @query.json
```

Ou use **Swagger** em `/docs` para testar com um array colado.

---

## Migrations (lembrete)

Gerar nova revisão a partir dos modelos (com banco acessível):

```bash
python -m alembic revision --autogenerate -m "descricao"
python -m alembic upgrade head
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
