"""CLI do worker ARQ compatível com Python 3.12+ / 3.14.

O `python -m arq ...` usa `asyncio.get_event_loop()` sem loop pré-existente; a partir do
Python 3.14 isso pode levantar RuntimeError (ver python-arq/arq#512). Este módulo cria
e registra o loop antes de `run_worker`.
"""

import asyncio

from arq.worker import run_worker

from app.infrastructure.messaging.arq_settings import WorkerSettings


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run_worker(WorkerSettings)


if __name__ == "__main__":
    main()
