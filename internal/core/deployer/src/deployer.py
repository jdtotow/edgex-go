import json, time, docker, os, requests, logging, pickle
from os import path 
from docker.types import Resources as DockerResources, RestartPolicy, EndpointSpec
from prometheus_client import CollectorRegistry, Gauge
from threading import Thread

MAX_MEM_PER_APPLICATION = int(os.environ.get("MAX_MEM_PER_APPLICATION","1000000000"))
MAX_CPU_PER_APPLICATION = int(os.environ.get("MAX_CPU_PER_APPLICATION","4")) 
CONSUL_HOSTNAME = os.environ.get("CONSUL_HOSTNAME_CLOUD","morphemic.cloud:9898")
EDGEX_CONSUL_HOSTNAME = os.environ.get("EDGEX_CONSUL_HOSTNAME","localhost")
EDGEX_CONSUL_URL = os.environ.get("EDGEX_CONSUL_URL","http://localhost:8500")
EDGEX_CONSUL_PORT = os.environ.get("EDGEX_CONSUL_PORT","8500")
DEPLOYER_HOSTNAME = os.environ.get("DEPLOYER_HOSTNAME","192.168.1.3")
DEPLOYER_PORT = os.environ.get("DEPLOYER_PORT","8778")

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

class DeviceManagement():
    def __init__(self):
        self.applications = {}
    
class ApplicationControlRoutine(Thread):
    def __init__(self,interval,deployer):
        self.interval = interval 
        self.deployer = deployer 
        super(ApplicationControlRoutine,self).__init__()
    def run(self):
        while True:
            missing_components_on_swarm = []
            components = self.deployer.getComponentsDeployed()
            services_running = self.deployer.getSwarmServices()
            if self.deployer.isDeploying():
                time.sleep(30)
                continue
            for component in components:
                if component.getName() not in services_running:
                    missing_components_on_swarm.append(component)
            if missing_components_on_swarm != []:
                self.deployer.missingComponents(missing_components_on_swarm)
            time.sleep(self.interval)

class ApplicationComponent():
    def __init__(self, name, image,_object,application_name):
        self.name = name 
        self.image = image 
        self.replicas = 0
        self.resource = None 
        self.env = [] 
        self.labels = {}
        self._object = _object
        self.application_name = application_name
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
    def setReplicas(self,number):
       self.replicas = number 
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
    def getObject(self):
        return self._object
    def getApplicationName(self):
        return self.application_name

class Application():
    def __init__(self, name):
        self.name = name 
        self.components = {}
        self.time = time.time()
        self.last_modifiction = time.time()
    def addComponent(self,component):
        if "name" in component and "image" in component:
            comp = ApplicationComponent(component["name"],component["image"],component,self.name)
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
        self.is_deploying = False 
    def connect(self):
        try:
            self.docker_client = docker.from_env()
        except:
            logging.error("Error while trying to connect to docker API")
            time.sleep(10)
            self.connect()
    def start(self):
        self.connect()
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
        if len(self.applications.keys()) > 0:
            logging.info("Previous configuation has been loaded")
            logging.debug(self.applications)
        routine = ApplicationControlRoutine(30,self)
        routine.start()
        self.registerToLocalConsul()
        logging.info("The deployer started successfully")

    def isDeploying(self):
        return self.is_deploying 

    def registerToLocalConsul(self):
        message = {'id':'deployer','name':'deployer','port': int(DEPLOYER_PORT)}
        message['check'] = {'name':'Deployer on port 8778','args':['tcp:'+DEPLOYER_HOSTNAME+':'+DEPLOYER_PORT],'interval':'30s','status':'passing'}
        try:
            response = requests.put(url=EDGEX_CONSUL_URL+"/v1/agent/service/register",data=json.dumps(message),headers={'Content-Type':'application/json'})
            print(response.text)
        except Exception as e:
            logging.error("An error occured")
            print(e)
    def createNetwork(self,name):
        try:
            for network in self.docker_client.networks.list():
                if network.name == name:
                    logging.info("Network {0} already exists".format(name))
                    return True 
            self.docker_client.networks.create(name,driver="bridge",scope="swarm")
            logging.info("Network {0} created".format(name))
            return True 
        except Exception as e:
            print(e)
            logging.error("Could not create network\nProcess will retry in 10s")
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
            logging.error("Could not get services\nReconnection in 10s")
            time.sleep(10)
            self.connect()
            self.getService(name)

    def getComponentsDeployed(self):
        result = []
        for app in self.applications.values():
            result.extend(app.getComponents())
        return result 
    def missingComponents(self,components):
        logging.info("{} component are missing on the execution environment".format(len(components)))
        for component in components:
            application_name = component.getApplicationName()
            _json = component.getObject()
            self.createNetwork(application_name)
            self.prepareDeploy(_json,application_name)
    def getSwarmServices(self):
        result = []
        try:
            for service in self.docker_client.services.list():
                result.append(service.name)
            return result 
        except Exception as e:
            logging.error(e)
            logging.error("Could not get services in docker swarm\nretry in 10s")
            time.sleep(10)
            self.connect()
            self.getSwarmServices()

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
        for name, application in self.applications.items():
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
                service.remove()
                del self.applications[_name]
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
            self.is_deploying = True 
            resources = DockerResources(mem_limit=mem_limit,mem_reservation=mem_reservation,cpu_limit=cpu_limit,cpu_reservation=cpu_reservation)
            restart_policy = RestartPolicy(condition=restart['name'],delay=10,max_attempts=restart['MaximumRetryCount'])
            endpoints = EndpointSpec(mode='vip',ports=ports)
            self.docker_client.services.create(image=image,name=service_name,hostname=service_name,restart_policy=restart_policy,endpoint_spec=endpoints,resources=resources,mounts=volumes,env=environment,labels=labels,command=command,networks=networks)
            logging.info("{0} component deployed".format(service_name))
            self.is_deploying = False 
            return resources
        except Exception as e:
            print(e)
            self.is_deploying = False 
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
                    app = self.applications[application_name]
                    for component in app.getComponents():
                        if component.getName() == component_name:
                            component.setReplicas(n_replicas)
                    
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

    


