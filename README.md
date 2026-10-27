# Protótipo: monolito + fila (Flask → Redis → worker Celery)

```
 navegador ──POST /tarefas──▶ Flask (app.py) ──.delay()──▶ Redis (fila)
     ▲                         │  responde "ID xyz" na hora     │
     │                         │                                ▼
     └──GET /tarefas/xyz───────┘◀──── status/resultado ──── worker Celery (tasks.py)
          (polling a cada 1s)
```

## Arquivos
- `app.py` – o monolito (Flask). Só enfileira e consulta status.
- `tasks.py` – a tarefa pesada + config do Celery. Importado pelo Flask **e** pelo worker.
- `templates/index.html` – página que cria tarefas e faz polling.

## Como rodar (3 terminais)

**1. Redis** (escolha um):
```bash
sudo pacman -S valkey && valkey-server        # Arch: Valkey é o fork do Redis, mesmo protocolo
# ou
docker run --rm -p 6379:6379 redis:7
```

**2. Worker:**
```bash
source .venv/bin/activate          # (se não existir: python -m venv .venv && pip install -r requirements.txt)
celery -A tasks worker --loglevel=info --concurrency=2
```

**3. Flask:**
```bash
source .venv/bin/activate
python app.py
```
Abra http://localhost:5000

## Experimentos para "sentir" o padrão
1. **Resposta imediata:** crie uma tarefa de 10s. Veja que a resposta HTTP chega em poucos ms.
2. **Fila de verdade:** clique "Enviar" 5 vezes rápido. Com `--concurrency=2`, só 2 rodam por vez; as outras ficam `PENDING` esperando.
3. **Escalar:** abra um 4º terminal com outro worker. As tarefas passam a andar mais rápido, sem mexer no Flask.
4. **Retry:** coloque chance de falha `0.7`. Veja no terminal do worker as novas tentativas (status `RETRY`) até dar certo ou estourar o limite de 3 (`FAILURE`).
5. **Worker caiu:** pare o worker (Ctrl+C), crie tarefas, e ligue de novo. Elas estavam esperando no Redis e são processadas.
6. **Redis caiu:** pare o Redis e tente criar uma tarefa. Aqui está o ponto fraco do desenho (é isso que "failover" resolve).
