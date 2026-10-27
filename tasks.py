"""
O "trabalho pesado" do monolito.

Este arquivo é importado por DOIS processos:
  - o Flask (app.py), que só ENFILEIRA tarefas com .delay()
  - o worker Celery, que de fato EXECUTA as tarefas

Mesmo código, mesmo repositório -> continua sendo um monolito.
"""
import random
import time

from celery import Celery

REDIS_URL = "redis://localhost:6379/0"

# broker  = onde a fila mora (Redis)
# backend = onde o resultado/status fica guardado (Redis também)
celery_app = Celery("prototipo", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_track_started=True,  # permite ver o status STARTED, não só PENDING -> SUCCESS
    result_expires=3600,      # resultados somem do Redis depois de 1h
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=2)
def processar(self, texto: str, segundos: int = 5, chance_falha: float = 0.0):
    """Simula uma tarefa lenta (ex: chamar uma IA, gerar um PDF, processar um áudio)."""
    # Reporta progresso no meio do caminho (o cliente vê isso no polling)
    for i in range(segundos):
        self.update_state(state="PROGRESS", meta={"atual": i + 1, "total": segundos})
        time.sleep(1)

    # Simula uma falha temporária (API externa fora do ar, timeout...) -> RETRY
    if random.random() < chance_falha:
        tentativa = self.request.retries + 1
        print(f"[worker] falhou na tentativa {tentativa}, tentando de novo...")
        raise self.retry(exc=RuntimeError(f"falha simulada na tentativa {tentativa}"))

    return {"original": texto, "resultado": texto.upper(), "tentativas": self.request.retries + 1}
