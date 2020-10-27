import json, os 
from flask import Flask, Response, request 
import requests, random 

ADDRESSABLE_REGISTRY_URL = os.environ.get("ADDRESSABLE_REGISTRY_URL","http://localhost:48081/api/v1/addressable")
VALUE_DESCRIPTION_URL = os.environ.get("VALUE_DESCRIPTION_URL","http://localhost:48080/api/v1/valuedescriptor")
device_name = "EDGEX-COMPUTELISTSUM"
size_list = 10
app = Flask(__name__) 

def makeValueDescription():
    value_desc = {
        "name":"sum",
        "description":"Sum of a list",
        "min":"0",
        "max":"1000000000",
        "type":"Int16",
        "uomLabel":"count",
        "defaultValue":"0",
        "formatting":"%s",
        "labels":["sum","list_sum"]
    }
    value_descriptor = requests.post(url=VALUE_DESCRIPTION_URL,data=json.dumps(value_desc),headers={'Content-Type':'application/json'}).text 
    print("value descriptor id={0} ".format(value_descriptor))

def makeAddressableObject():
    addr_object = {
        "name": device_name,
        "protocol":"HTTP",
        "address":"localhost",
        "port":8877,
        "path":"/",
        "publisher":"none",
        "user":"none",
        "password":"none",
        "topic":"none"
    }
    addressable_object = requests.post(url=ADDRESSABLE_REGISTRY_URL,data=json.dumps(addr_object),headers={'Content-Type':'application/json'}).text 
    print("Addressable id={0}".format(addressable_object))
def makeDeviceDescriptor():
    file = open('./device-descriptor.yaml','rb')
    files = {'file': file}
    #print(file.read())
    response = requests.post(url="http://localhost:48081/api/v1/deviceprofile/uploadfile",files=files,data={'file': 'device-descriptor.yaml'})
    print("Device description added",response.text)

def deviceRegistration():
    _data = {
        "name":"Sum list computer",
        "description":"This device compute the sum of list",
        "labels":["sum_list","sum"],
        "adminState":"unlocked",
        "operatingState":"enabled",
        "addressable":  {"name": device_name}
    }
    response = requests.post(url="http://localhost:48081/api/v1/deviceservice",data=json.dumps(_data),headers={'Content-Type':'application/json'})
    print("Registration of the device finished",response.text)

def registerServiceDevice():
    _data = {
        "name":"sumlist",
        "description": "compute sum of a list #1",
        "adminState":"unlocked",
        "operatingState":"enabled",
        "protocols":
            {"vDevice protocol":
                {"device address":"local"}
            },
        "labels": ["sum_list","sum"],
        "location":"",
        "service":{"name":"Sum list computer"},
        "profile":{"name":"Sum computer from list"}
    }
    response = requests.post(url="http://localhost:48081/api/v1/device",data=json.dumps(_data),headers={'Content-Type':'application/json'})
    print("Service sum list registered {0}".format(response.text))

@app.route('/',methods=['GET','POST','PUT'])
def home():
    return Response("Virtual device edgex on 8877",status=200,mimetype="application/json")

@app.route('/api/v1/devices/<deviceId>/set_size',methods=['GET','PUT'])
def event(deviceId):
    global size_list
    print(request.args.get('Size'))
    print("device id = ", deviceId)
    size_list = int(request.args.get('Size'))
    print("The size has been modified , new size = {0}".format(size_list))
    return Response(str(size_list),status=200,mimetype="application/json")

#/api/v1/devices/87887d80-a5e1-4274-a10b-3a236fad0de3/read_s
@app.route('/api/v1/devices/<deviceId>/read_sum')
def read_sum_v1(deviceId):
    print("device id = ",deviceId)
    _list = [random.randint(2,10) for i in range(size_list)]
    return Response(str(sum(_list)),status=200,mimetype="application/json")
def read():
    _list = [random.randint(2,10) for i in range(size_list)]
    return Response(str(sum(_list)),status=200,mimetype="application/json")

@app.route('/api/v1/devices/<deviceId>/get_size',methods=['GET','POST'])
def get_size(deviceId):
    print("device id = ",deviceId)
    return Response(str(size_list),status=200,mimetype="application/json")

if __name__ == "__main__":
    #makeAddressableObject()
    #makeValueDescription()
    #makeDeviceDescriptor()
    #deviceRegistration()
    #registerServiceDevice()
    app.run('0.0.0.0',port=8877)