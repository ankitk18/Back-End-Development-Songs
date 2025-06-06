from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################


@app.route("/health")
def health():
    return {"status":"OK"}, 200

@app.route("/count")
def count():
    doc = len(songs_list)
    return {"count":doc}, 200

@app.route("/song", methods=['GET'])
def songs():
    x = db.songs.find({})
    return json_util.dumps({"song": x}), 200

@app.route("/song/<int:id>", methods=['GET'])
def get_song_by_id(id):
    song = db.songs.find({"id":id})
    if song:
        return json_util.dumps({"message": song}),200
    else:
        return {"message":"song with id not found"},404

@app.route("/song", methods=['POST'])
def create_song():
    res = request.get_json()
    findS = db.songs.find_one({"id":res["id"]})
    if findS:
        return {"Message":f"song with id {res['id']} already present"},302
    else:
        rs = db.songs.insert_one(res)
        return {"inserted_id": str(rs.inserted_id)}, 201

@app.route("/song/<int:id>", methods=['PUT'])
def update_song(id):
    res = request.get_json()
    changes = {"$set":res}
    check = db.songs.find_one({"id":id})
    matched = False
    if not check:
        return {"message":"song not found"},404
    
    no_change = all(check.get(key) == res[key] for key in res)

    if no_change:
        return {"message":"song found, but nothing updated"},200
    
    db.songs.update_one({"id": id}, changes)
    updatedOne = db.songs.find_one({"id": id})
    return json_util.dumps(updatedOne), 201
@app.route("/song/<int:id>", methods=['DELETE'])
def delete_song(id):
    rs = db.songs.delete_one({"id":id})

    if rs.deleted_count == 0:
        return jsonify({"message": "song not found"}),404
    else:
        return "",204