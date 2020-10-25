from flask import Flask, Response, request 
from flask_jwt import JWT, jwt_required, current_identity
import time , json, hashlib, binascii, os, logging 
from pymongo import MongoClient
from werkzeug.security import safe_str_cmp
from deployer import Deployer
from prometheus_client.exposition import CONTENT_TYPE_LATEST, generate_latest

MONGODB_HOSTNAME = os.environ.get("MONGODB_HOSTNAME","localhost")
MONGODB_PORT = os.environ.get("MONGODB_PORT","27017")

log = logging.getLogger('console')
#log.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
app = Flask(__name__) 

deployer = Deployer()
deployer.start()

username_table = {}
userid_table = {}
client = None 

class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password
    def __str__(self):
        return "User(id='%s')" % self.id

def connectToMongoDB():
    connected_mongo_db = False 
    interval_reconnect = 10
    global client 
    while not connected_mongo_db:
        try:
            client = MongoClient('mongodb://'+MONGODB_HOSTNAME+':'+MONGODB_PORT+'/')
            connected_mongo_db = True 
        except Exception as e:
            print(e)
            logging.error("Cannot connect to MONGODB\nRetry in {0}s".format(interval_reconnect))
            time.sleep(interval_reconnect)
            interval_reconnect *= 2

def loadUsers():
    global client, userid_table, username_table
    db = client['edgex']
    users_collection = db['users']
    users = users_collection.find({})
    for u in users:
        username_table[u['username']] = User(u['id'],u['username'],u['password'])
        userid_table[u['id']] = User(u['id'],u['username'],u['password'])
    log.info("Users loaded")

def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')
 
def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def authenticate(username, password):
    if userid_table == None:
        return None 
    user = username_table.get(username, None)
    #if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
    #   return user
    if user and verify_password(user.password, password):
        return user
def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)

#connection to MongoDB
connectToMongoDB()
app.config['SECRET_KEY'] = 'super-secret-key'
jwt = JWT(app, authenticate, identity)
loadUsers()

#endpoints 
@app.route('/', methods=['GET','POST'])
def home():
    return Response("Deployer is listening on 8778", status=200, mimetype="application/json")

@app.route('/get_applications',methods=['GET','POST'])
@jwt_required()
def get_applications():
    applications = deployer.getApplicationsDeployed()
    return Response(json.dumps(applications), status=200, mimetype="application/json")

@app.route('/endpoints',methods=['GET','POST'])
@jwt_required()
def get_endpoints():
    response = {
        'get_applications':'get all applications deployed on the edge node [GET,POST]',
        'deploy':'deploy an application [POST]',
        'get_application':'get application status [GET,POST]',
        'undeploy':'undeploy application [DELETE]',
        'scale': 'scale an application [POST]'
    }
    return Response(json.dumps(response),status=200,mimetype="application/json")

@app.route('/deploy',methods=['POST'])
@jwt_required()
def deploy():
    _data = None 
    try:
        _data = request.get_json() 
    except:
        return Response("bad request",status=500,mimetype="application/json")
    response = deployer.addApplication(_data)
    return Response(json.dumps(response),status=200,mimetype="application/json")

@app.route('/undeploy',methods=['DELETE'])
@jwt_required()
def undeploy():
    name = request.json["name"]
    if name == None:
        return Response("bad request",status=500, mimetype="application/json")
    response = deployer.deleteApplication(name)
    return Response(json.dumps(response),status=200,mimetype="application/json")

@app.route('/metrics',methods=['GET'])
def metrics():
    registry = deployer.getRegister()
    collected_metric = generate_latest(registry)
    return Response(collected_metric,status=200,mimetype=CONTENT_TYPE_LATEST)

@app.route('/register',methods=['POST'])
def register():
    username, password = None, None
    try: 
        username = request.json['username']
        password = request.json['password'] 
    except:
        return Response("Bad request",status=400,mimetype="application/json")

    db = client["edgex"]
    users_collection = db["users"]
    if users_collection.find({"username": username}).count() > 0:
        return Response('The current user already registered', status=200, mimetype="application/json")
    user = {"username": username,"password": hash_password(password), "id": users_collection.find({}).count()+1}
    users_collection.insert_one(user)
    loadUsers()
    return Response('User registered', status=200, mimetype="application/json")

if __name__ == '__main__':
    app.run('0.0.0.0', port=8778, debug=True)
    