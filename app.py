from flask import Flask, request, Response
from tasks import *
import json
import os

app = Flask(__name__)

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return Response(status=200)

@app.route('/Tarefa', methods=['GET', 'POST'])
def Tarefa():
    global task_dict
    global id_dict
    if request.method == 'POST':
        data = request.get_json(force=True)
        t = Tarefas(id_dict, data["nome"])
        task_dict[id_dict] = t
        id_dict += 1
        return json.dumps([task.__dict__ for task in list(task_dict.values())]), 201
    else:
        return json.dumps([task.__dict__ for task in list(task_dict.values())]), 200

@app.route('/Tarefa/<id_key>', methods=['GET', 'PUT', 'DELETE'])
def tarefa_id(id_key):
    global task_dict
    global id_dict
    id = int(id_key)

    if request.method == 'PUT':
        data = request.get_json(force=True)
        if id in task_dict:
            t = Tarefas(id, data["nome"])
            task_dict[id] = t
            return Response(status=200)
        else:
            return Response(status=204)
    elif request.method == 'DELETE':
        if id in task_dict:
            del task_dict[id]
            return Response(status=200)
        else:
            return Response(status=204)
    else:
        return json.dumps(task_dict[int(id)].__dict__)

app.run(host=os.environ["APP_URL"], port=5000)
