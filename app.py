from flask import Flask, request, Response
import json
import os
import firebase_admin
from firebase_admin import db

app = Flask(__name__)
cred = firebase_admin.credentials.Certificate("./firebase_keys.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://cloudprojeto-27847.firebaseio.com/'
})
ref = db.reference('/')

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return Response(status=200)

@app.route('/Tarefa', methods=['GET', 'POST'])
def Tarefa():
    if request.method == 'POST':
        data = request.get_json(force=True)
        tarefas_ref = ref.child('tarefas')
        add = tarefas_ref.push(data)
        return add.key, 201
    else:
        tarefas_ref = ref.child('tarefas').get()
        return json.dumps(tarefas_ref), 200

@app.route('/Tarefa/<id_key>', methods=['GET', 'PUT', 'DELETE'])
def tarefa_id(id_key):
    if request.method == 'PUT':
        data = request.get_json(force=True)
        tarefas_ref = ref.child('tarefas')
        update_ref = tarefas_ref.child(id_key)
        if (update_ref.get()):
            update_ref.update(data)
            return json.dumps(tarefas_ref.child(id_key).get()), 200
        else:
            return "None", 404
    elif request.method == 'DELETE':
        tarefas_ref = ref.child('tarefas')
        delete_ref = tarefas_ref.child(id_key).delete()
        return "OK", 200
    else:
        tarefas_ref = ref.child('tarefas')
        get = tarefas_ref.child(id_key).get()
        if (get):
            return json.dumps(get), 200
        else:
            return "None", 404

app.run(host=os.environ["APP_URL"], port=5000)
