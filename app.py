"""
O monolito: uma única aplicação Flask que atende o usuário.

Ela NUNCA faz o trabalho pesado dentro da requisição. Só:
  1. joga a tarefa na fila (Redis)
  2. devolve o ID na hora
  3. responde "como está a tarefa X?" quando o cliente pergunta (polling)
"""
from flask import Flask, jsonify, render_template, request

from tasks import celery_app, processar

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/tarefas")
def criar_tarefa():
    dados = request.get_json(force=True)
    tarefa = processar.delay(
        dados.get("texto", ""),
        int(dados.get("segundos", 5)),
        float(dados.get("chance_falha", 0.0)),
    )
    # Responde em milissegundos, mesmo que a tarefa leve minutos
    return jsonify({"id": tarefa.id, "status": "na fila"}), 202


@app.get("/tarefas/<tarefa_id>")
def status_tarefa(tarefa_id):
    r = celery_app.AsyncResult(tarefa_id)
    resposta = {"id": tarefa_id, "status": r.state}
    if r.state == "PROGRESS":
        resposta["progresso"] = r.info
    elif r.state == "SUCCESS":
        resposta["resultado"] = r.result
    elif r.state in ("FAILURE", "RETRY"):
        resposta["erro"] = str(r.info)
    return jsonify(resposta)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
