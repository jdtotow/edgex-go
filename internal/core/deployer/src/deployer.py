import json, time, docker, os, pickle
from os import path 
from docker.types import Resources as DockerResources, RestartPolicy, EndpointSpec
from prometheus_client import CollectorRegistry, Gauge

MAX_MEM_PER_APPLICATION = int(os.environ.get("MAX_MEM_PER_APPLICATION","1000000000"))
MAX_CPU_PER_APPLICATION = int(os.environ.get("MAX_CPU_PER_APPLICATION","4")) 
CONSUL_HOSTNAME = os.environ.get("CONSUL_HOSTNAME_CLOUD","morphemic.cloud:9898")


class ApplicationComponent():
    def __init__(self, name, image):
        self.name = name 
        self.image = image 
        self.replicas = 0
        self.resource = None 
        self.env = [] 
        self.labels = {}
    def setResource(self,resource):
        self.resource = resource
    def getName(self):
        return self.name 
    def getImage(self):
        return self.image 
    def getResource(self):
        return self.resource
    def setReource(self,resource):
        self.resource = resource 
    def getReplicas(self):
        return self.replicas
    def increaseReplicas(self):
        self.replicas +=1
    def decreaseReplicas(self):
        self.replicas -=1
    def addEnvs(self,env):
        self.env = env 
    def addLabels(self,labels):
        self.labels = labels 
    def addEnv(self, _key, _value):
        if self.env == None:
            self.env = []
        self.env.append(_key+"="+_value)
    def getEnv(self,_key):
        for k in self.env:
            if k == self.env[:k.index("=")]:
                return self.env[k.index("="):]
        return None 
    def addLabel(self,_key, _value):
        if self.labels == None:
            self.labels = {}
        self.labels[_key] = _value
    def getLabels(self,_key):
        if self.labels[_key]:
            return self.labels[_key]
        return None 
    def getResource(self):
        return self.resource

class Application():
    def __init__(self, name):
        self.name = name 
        self.components = {}
        self.time = time.time()
        self.last_modifiction = time.time()
    def addComponent(self,component):
        if "name" in component and "image" in component:
            comp = ApplicationComponent(component["name"],component["image"])
            if "labels" in component:
                comp.addLabels(component["labels"])
            if "env" in component:
                comp.addEnvs(component["env"])
            self.components[component["name"]] = comp 
            return comp 
    def getComponents(self):
        return list(self.components.values())

    def getComponent(self,name):
        if name in self.components:
            return self.components[name]
        return None 
    def updateLastModification(self):
        self.last_modifiction = time.time()
    def toJSON(self):
        return {"name": self.name,"create at": self.time,"last_modification": self.last_modifiction,"N.component": len(self.components)}
    def __repr__(self):
        return json.dumps(self.toJSON())

class Deployer():
    def __init__(self):
        self.applications = {}
        self.docker_client = None
        self.metrics_registry = CollectorRegistry()
        self.metric_n_applications = None 
    def connect(self):
        try:
            self.docker_client = docker.from_env()
        except:
            print("Error while trying to connect to docker API")
            time.sleep(10)
            self.connect()
    def start(self):
        self.connect()
        print("The deployer started successfully")
        #number of application deployed metric
        self.metric_n_applications = Gauge('number_applications','Number of applications deployed',labelnames=['application'],registry=self.metrics_registry)
        self.metric_n_applications.labels(application='deployer').set(0)
        #start time metric
        start_time = Gauge('start_time','startint time',labelnames=['application'],registry=self.metrics_registry)
        start_time.labels(application='deployer').set(time.time())
        if path.isfile("../data/applications.pk1"):
            file = open("../data/applications.pk1","rb")
            self.applications = pickle.load(file)
            file.close()
    def createNetwork(self,name):
        try:
            for network in self.docker_client.networks.list():
                if network.name == name:
                    print("Network {0} already exists".format(name))
                    return True 
            self.docker_client.networks.create(name,driver="bridge",scope="swarm")
            print("Network {0} created".format(name))
            return True 
        except Exception as e:
            print(e)
            print("Could not create network\nProcess will retry in 10s")
            time.sleep(10)
            self.connect()
            self.createNetwork(name)
    def getService(self,name):
        try:
            for service in self.docker_client.services.list():
                if service.name == name:
                    return service
            return None 
        except:
            print("Could not get services\nReconnection in 10s")
            time.sleep(10)
            self.connect()
            self.getService(name)

    def getApplication(self,name):
        if name in self.applications:
            return self.applications[name]
        return None 
    def addApplication(self,application):
        if "name" in application:
            app = Application(application["name"])
            self.createNetwork(application["name"])
            if "components" in application:
                for i in range(len(application["components"])):
                    #trying to deploy component 
                    component = application["components"][i]
                    res = self.prepareDeploy(component,application["name"])
                    if res != None:
                        app_component = app.addComponent(component)
                        app_component.setResource(res)
            self.applications[application["name"]] = app 
            self.metric_n_applications.labels(application='deployer').set(len(self.applications.keys()))
            file = open("../data/applications.pk1","wb")
            pickle.dump(self.applications,file,pickle.HIGHEST_PROTOCOL)
            file.close()
            return {"details": app.toJSON()}

    def getApplicationsDeployed(self):
        return list(self.applications.keys())

    def deleteApplication(self,_name):
        components_name = []
        for name, application in self.applications:
            if name == _name:
                components = application.getComponents()
                for component in components:
                    components_name.append(component.getName())
        if components_name == []:
            return {"status": "error", "message": "No application component found"}
        try:
            self.docker_client.ping()
        except:
            self.connect()
        for service in self.docker_client.services.list():
            if service.name in components_name:
                service.delete()
        for network in self.docker_client.networks.list():
            if network.name == _name:
                network.remove()
        file = open("../data/applications.pk1","wb")
        pickle.dump(self.applications,file,pickle.HIGHEST_PROTOCOL)
        file.close()
        return {"status":"success","message": "{0} removed".format(components_name)}

    def prepareDeploy(self,component,application_name):
        service_name = component["name"]
        image = component["image"]
        ports = {}
        for port in component["ports"]:
            ports[port] = port 
        restart = component["restart"]
        cpu_limit = component["resource"]["cpu_limit"]
        cpu_reservation = component["resource"]["cpu_reservation"]
        mem_limit = component["resource"]["mem_limit"]
        mem_reservation = component["resource"]["mem_reservation"]
        volumes = [] #volumes are not supported yet 
        environment = component["env"]
        labels = component["labels"]
        command = component["command"]
        networks = [application_name]
        return self.createService(service_name,image,ports,restart,cpu_limit,cpu_reservation,mem_reservation,mem_limit,volumes,environment,labels,command,networks)

    def createService(self,service_name,image,ports,restart,cpu_limit,cpu_reservation,mem_reservation,mem_limit,volumes,environment,labels,command,networks):
        try:
            resources = DockerResources(mem_limit=mem_limit,mem_reservation=mem_reservation,cpu_limit=cpu_limit,cpu_reservation=cpu_reservation)
            restart_policy = RestartPolicy(condition=restart['name'],delay=10,max_attempts=restart['MaximumRetryCount'])
            endpoints = EndpointSpec(mode='vip',ports=ports)
            self.docker_client.services.create(image=image,name=service_name,hostname=service_name,restart_policy=restart_policy,endpoint_spec=endpoints,resources=resources,mounts=volumes,env=environment,labels=labels,command=command,networks=networks)
            print("{0} component deployed".format(service_name))
            return resources
        except Exception as e:
            print(e)
            return None 
    def getRegister(self):
        return self.metrics_registry
    def scale(self,_data):
        _type = _data["type"]
        application_name = _data["application_name"]
        component_name = _data["component_name"]
        if _type == "horizontal":
            n_replicas = _data["replicas"]
            for service in self.docker_client.services.list():
                if service.name == component_name:
                    service.scale(n_replicas) 
                    
        elif _type == "vertical":
            cpu_limit = _data["cpu_limit"]
            cpu_reservation = _data["cpu_reservation"]
            mem_limit = _data["mem_limit"]
            mem_reservation = _data["mem_reservation"]
            for service in self.docker_client.services.list():
                if service.name == component_name:
                    resources = DockerResources(mem_limit=mem_limit,mem_reservation=mem_reservation,cpu_limit=cpu_limit,cpu_reservation=cpu_reservation)
                    service.update(resources)
        else:
            pass 

        app = self.applications[application_name]
        app.updateLastModification()
        return {"status":"success", "massage":"Component {0} of the application {1} has been modified".format(component_name,application_name)}

    


