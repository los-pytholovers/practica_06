import os.path
import random
from datetime import datetime
from bson import ObjectId

from flask import Flask, jsonify, abort, make_response, request
from flask_cors import CORS
from gridfs.synchronous.grid_file import GridFS
from werkzeug.utils import append_slash_redirect

app = Flask(__name__)
CORS(app)

wsgi_app = app.wsgi_app

from pymongo import MongoClient
#Create connection with DB
def contextDB():
    conex = MongoClient(host=['127.0.0.1:27017'])
    conexDB = conex.Mercado_de_Artesanos_de_Puntarenas
    return conexDB

#Create local API functions
def token():
    ahora = datetime.now()
    antes = datetime.strptime("1970-01-01", "%Y-%m-%d")
    return str(hex(abs((ahora - antes).seconds) * random.randrange(10000000)).split('x')[-1]).upper()

def tokObras():
    ahora = datetime.now()
    antes = datetime.strptime("1970-01-01", "%Y-%m-%d")
    return str(hex(abs((ahora - antes).seconds) * random.randrange(1000000000)).split('x')[-1]).upper()

#Error handling
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad Request...!'}), 400)

@app.errorhandler(401)
def unauthorized(error):
    return make_response(jsonify({'error': 'Unauthorized....!'}), 401)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not Found....!'}), 404)

@app.errorhandler(500)
def internalServerE(error):
    return make_response(jsonify({'error': 'Internal Server Error....!'}), 500)

#Create routes and artist control functions
#................................................................
#Register artist's

@app.route('/registrarArtista', methods=['POST'])
def createArtist():
    if not request.json or \
            not 'nombre' in request.json or \
            not 'email' in request.json or \
            not 'telefono' in request.json or \
            not 'direccion' in request.json or \
            not 'categoria' in request.json:
        abort(400)

    id_token = token()
    artist = {
        "_id": id_token,
        'nombre': request.json['nombre'],
        'email': request.json['email'],
        'telefono': request.json['telefono'],
        'direccion': request.json['direccion'],
        'categoria': request.json['categoria']
    }
    data = {
        "status": 201,
        "status_msg": "Data creada",
        "data": artist
    }
    try:
        conex = contextDB()
        conex.artistas.insert_one(artist)
    except Exception as exc:
        print(exc)
        abort(500)
    return jsonify(data), 201

#Update artist's data
@app.route('/actualizarArtista/<string:artist_id>', methods=['PUT'])
def actualizarArtista(artist_id):
    try:
        conex = contextDB()
        datos = conex.artistas.find_one({"_id":{"$eq":artist_id}})
        if datos == None:
            abort(404)
        if 'nombre' not in request.json or request.json['nombre'] == '':
            abort(400)
        if 'email' not in request.json or request.json['email'] == '':
            abort(400)
        if 'telefono' not in request.json or request.json['telefono'] == '':
            abort(400)
        if 'direccion' not in request.json or request.json['direccion'] == '':
            abort(400)
        if 'categoria' not in request.json or request.json['categoria'] == '':
            abort(400)

        conex.artistas.update_one({'_id': artist_id},
                                {'$set': {
                                  'nombre': request.json['nombre'],
                                  'email': request.json['email'],
                                  'telefono': request.json['telefono'],
                                  'direccion': request.json['direccion'],
                                  'categoria': request.json['categoria']
                                }})
    except Exception as exc:
        print(exc)
        abort(500)
    return jsonify({"status": 200,
                    "status_msg": "Ok",
                   "modified": True})

@app.route('/eliminarArtista/<string:artist_id>', methods=['DELETE'])
def eliminarArtista(artist_id):
    try:
        conex = contextDB()
        datos = conex.artistas.find_one({'_id':{'$eq':artist_id}})
        if datos == None:
            abort(404)
        conex.artistas.delete_one({'_id': datos['_id']})
    except Exception as exc:
        abort(404)
    return jsonify({'status': 200,
                    'status_msg': 'Ok',
                    'deleted': True})


@app.route('/<string:token>/ingresarObra', methods=['POST'])
def crear_obra(token):
    if not request.files or 'imagen' not in request.files or \
            not '_id' in request.form or \
            not 'nombreObra' in request.form:
        abort(400)

    imagen = request.files['imagen']

    conex = contextDB()
    fs = GridFS(conex)
    id_obra = tokObras()
    imagen_id = fs.put(imagen, filename=imagen.filename, content_type=imagen.content_type)

    obra = {
        '_id': id_obra,
        'nombreObra': request.form['nombreObra'],
        'imagen_Obra': imagen_id,
        'token': token
    }

    data = {
        "status": 201,
        "status_msg": "Data creada",
        "data": obra
    }

    try:
        conex = contextDB()
        conex.obras.insert_one(obra)
    except Exception as exc:
        print(exc)
        abort(500)

    def objectid_to_str(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: objectid_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [objectid_to_str(i) for i in obj]
        return obj

    data['data'] = objectid_to_str(data['data'])
    return jsonify(data), 201




@app.route('/<string:token>/eliminarObra/<string:id_obra>', methods=['DELETE'])
def eliminarObra(id_obra):
    try:
        conex = contextDB()
        fs = GridFS(conex)

        id_obra_obj = ObjectId(id_obra)

        datos = conex.obras.find_one({'_id': id_obra_obj})
        if datos is None:
            abort(404)

        fs.delete(datos['imagen_Obra'])
        conex.obras.delete_one({'_id': id_obra_obj})

    except Exception as exc:
        print(exc)
        abort(500)

    return jsonify({
        'status': 200,
        'status_msg': 'Ok',
        'deleted': True
    })


@app.route('/<string:token>/actualizarObra/<string:id_obra>', methods=['PUT'])
def actualizarObra(token, id_obra):
    try:
        conex = contextDB()
        fs = GridFS(conex)
        datos = conex.obras.find_one({'_id': id_obra})
        if datos is None:
            abort(404)
        if 'nombreObra' not in request.form or request.form['nombreObra'] == '':
            abort(400)

        nueva_imagen = request.files.get('imagen')
        if nueva_imagen:
            fs.delete(datos['imagen_Obra'])
            nueva_imagen_id = fs.put(nueva_imagen, filename=nueva_imagen.filename, content_type=nueva_imagen.content_type)
            datos['imagen_Obra'] = nueva_imagen_id

        conex.obras.update_one(
            {'_id': id_obra},
            {'$set': {
                'nombreObra': request.form['nombreObra'],
                'imagen_Obra': datos['imagen_Obra']
            }}
        )
    except Exception as exc:
        print(exc)
        abort(500)
    return jsonify({
        "status": 200,
        "status_msg": "Ok",
        "modified": True
    })


from bson import ObjectId

from bson import ObjectId
from flask import jsonify, abort


@app.route('/<string:token>/obtenerObra/<string:id_obra>', methods=['GET'])
def obtenerObra(token, id_obra):
    try:
        if len(id_obra) != 24:
            id_obra = id_obra.ljust(24, '0')

        if not ObjectId.is_valid(id_obra):
            abort(400, description="Invalid ObjectId format")

        conex = contextDB()
        datos = conex.obras.find_one({'_id': ObjectId(id_obra)})

        if datos is None:
            abort(404, description="Obra not found")

        return jsonify({
            "status": 200,
            "status_msg": "Ok",
            "data": {
                "_id": str(datos["_id"]),
                "nombreObra": datos["nombreObra"],
                "imagen_Obra": str(datos["imagen_Obra"])
            }
        })
    except Exception as exc:
        print(exc)
        abort(500, description="Internal server error")


@app.route('/<string:token>/obrasPorCategoria/<string:categoria>', methods=['GET'])
def obtenerObrasPorCategoria(token, categoria):
    try:
        conex = contextDB()
        fs = GridFS(conex)
        obras_cursor = conex.obras.find({'categoria': categoria})
        obras = list(obras_cursor)
        if not obras:
            print('No hay obras con tal categoria')
            abort(404)

        lista_obras = []
        for obra in obras:
            imagen_url = f"/{token}/imagen/{obra['imagen_Obra']}"
            lista_obras.append({
                "_id": str(obra["_id"]),
                "nombreObra": obra["nombreObra"],
                "imagen_url": imagen_url
            })
        return jsonify({
            "status": 200,
            "status_msg": "Ok",
            "data": lista_obras
        })
    except Exception as exc:
        print(exc)
        abort(500)

@app.route('/<string:token>/detalleObra/<string:id_obra>', methods=['GET'])
def obtenerDetalleObra(token, id_obra):
    try:
        conex = contextDB()
        fs = GridFS(conex)

        obra = conex.obras.find_one({'_id': id_obra})
        if obra is None:
            abort(404)

        imagen_url = f"/{token}/imagen/{obra['imagen_Obra']}"

        artista = conex.artistas.find_one({'_id': obra['token']})
        if artista is None:
            abort(404)
        return jsonify({
            "status": 200,
            "status_msg": "Ok",
            "data": {
                "obra": {
                    "_id": str(obra["_id"]),
                    "nombreObra": obra["nombreObra"],
                    "imagen_url": imagen_url,
                    "categoria": obra.get("categoria", "Sin categoría"),
                    "token": obra["token"]
                },
                "artista": {
                    "_id": str(artista["_id"]),
                    "nombre": artista["nombre"],
                    "email": artista["email"],
                    "telefono": artista["telefono"],
                    "direccion": artista["direccion"],
                    "categoria": artista["categoria"]
                }
            }
        })
    except Exception as exc:
        print(exc)
        abort(500, description="Internal server error")


if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 5000
    app.run(HOST, PORT)
