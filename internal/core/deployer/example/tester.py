import json, requests

file = open("application.json","r")
#_json = json.loads(content.read())

url = "http://localhost:8778"
headers_request = {"Content-Type": "application/json"}
credential = {'username': 'admin-2', 'password': 'admin-2'}

def register():
    response = requests.post(url+"/register",data = json.dumps(credential),headers=headers_request)
    print(response.text)

def login():
    global headers_request
    response = requests.post(url+"/auth", data = json.dumps(credential),headers=headers_request)
    _json = None 
    print(response.text)
    try:
        _json = json.loads(response.text)
    except:
        raise RuntimeError("An error occured")
    if 'status_code' in _json and _json['status_code'] == 401:
        raise RuntimeError(_json['error'])
    headers_request['Authorization'] = "JWT "+ _json['access_token']

content = file.read()
file.close()

register()
while True:
    response = requests.post(url=url + "/deploy",data=content,headers=headers_request)
    #response = requests.delete(url=url + "/undeploy",data=json.dumps({'name':'flask'}),headers=headers_request)
    try:
        _json = json.loads(response.text)
        print(_json)
    except Exception as e:
        print(e)
    if 'status_code' in _json and _json['status_code'] == 401:
        login()
    else:
        print(response.text)
        break 