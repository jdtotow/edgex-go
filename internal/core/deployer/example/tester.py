import json, requests

content = open("application.json","r")
#_json = json.loads(content.read())

response = requests.post(url="http://localhost:8778/deploy",data=content.read(),headers={'Content-Type':'application/json'})
print(response.text)