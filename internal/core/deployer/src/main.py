from flask import Flask, Response, request 
import time , json  
from deployer import Deployer
from prometheus_client.exposition import CONTENT_TYPE_LATEST, generate_latest

app = Flask(__name__) 

deployer = Deployer()
deployer.start()

#endpoints 
@app.route('/', methods=['GET','POST'])
def home():
    return Response("Deployer is listening on 8778", status=200, mimetype="application/json")

@app.route('/get_applications',methods=['GET','POST'])
def get_applications():
    applications = deployer.getApplicationsDeployed()
    return Response(json.dumps(applications), status=200, mimetype="application/json")

@app.route('/endpoints',methods=['GET','POST'])
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
def deploy():
    _data = None 
    try:
        _data = request.get_json() 
    except:
        return Response("bad request",status=500,mimetype="application/json")
    response = deployer.addApplication(_data)
    return Response(json.dumps(response),status=200,mimetype="application/json")

@app.route('/undeploy',methods=['DELETE'])
def undeploy():
    name = request.args.get("name")
    if name == None:
        return Response("bad request",status=500, mimetype="application/json")
    response = deployer.deleteApplication(name)
    return Response(json.dumps(response),status=500,mimetype="application/json")

@app.route('/metrics',methods=['GET'])
def metrics():
    registry = deployer.getRegister()
    collected_metric = generate_latest(registry)
    return Response(collected_metric,status=200,mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    app.run('0.0.0.0', port=8778, debug=True)
    