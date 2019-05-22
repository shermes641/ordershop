# OVERVIEW:


This is my attempt to take the master branch in the ordershop repo and run it on KUBERNETES.
It uses Replica Sets, Persistent Volumes, and Services to make this scalable.
It will run using **docker-compose** or can be deployed to a **Kubernetes Cluster**.

I hope this can server as an archetype for a microservice based architecture.

#### 2019-05-22

I have fixed all the known problems with this branch. I am stopping development on it now.

I did all my development on on a Windows 10 box running Docker Desktop Community  

# OrderShop:

Redis as an event store in a microservices architecture.

##### Steps to run from DOCKER (run from the project root directory)

1. Clean build `docker-compose build --no-cache`

2. Start the application by `docker-compose up`.

3. Install dependencies by `pip3 install -r client/requirements.txt`.

4. Execute the client by `python -m unittest client/client.py`.   #or py -3

5. Stop services  `docker-compose stop crm-service`

6. Run step 4. again

7. Be sure to stop all containers

There should be no failures

    ----------------------------------------------------------------------
    Ran 10 tests in 0.975s
    
    OK
    
# OrderShop on Kubernetes:

###### Note I did all my development on on a Windows 10 box running Docker Desktop Community  

    Version 2.0.0.3 (31259)
    Channel: stable
    Build: 8858db3 

##### I deployed to the "docker-for-desktop" cluster in the "default" namespace. You might make your own cluster and namespace and change the yaml files accordingly.
         
#### Apply all the yaml files in the root dir.
###### Note: the `error validating "docker-compose.yml"` error is expected --- you may get imutable errors also - ignore these
######        Assumes you ran all the steps above in Steps to run from DOCKER            

    >kubectl apply -f .
   
    deployment.extensions "billing-service" created
    service "billing-service" created
    deployment.extensions "crm-service" created
    service "crm-service" created
    deployment.extensions "customer-service" created
    service "customer-service" created
    deployment.extensions "gateway-api" created
    service "gateway-api-service" created
    deployment.extensions "inventory-service" created
    service "inventory-service" created
    deployment.extensions "msg-service" created
    service "msg-service" created
    deployment.extensions "order-service" created
    service "order-service" created
    deployment.extensions "product-service" created
    service "product-service" created
    deployment.apps "redis" created
    persistentvolume "redis-pv1-volume" created
    persistentvolumeclaim "redis-pv1-claim" created
    service "redis" created
    error validating "docker-compose.yml": error validating data: [apiVersion not set, kind not set]; if you choose to ignore these errors, turn validation off with --validate=false
            
 #### Once all the deployments are running you can test it
 
 ![kubectl proxy](./dashboard.png?raw=true "KUBERNETES DASHBOARD")
 
 ##### Steps to run from KUBERNETES (run from the project root directory)
    
1. You will need to delete all of the running pods except **redis** when you run this multiple times.

2. Execute the client by `python -m unittest client/client.py`.   #or py -3  

There should be no failures 
      
      
# NOTES:

The **DOCKER** version of redis is not persistent, but the **KUBERNETES** version is.

There are a few assumptions. 

1. **KUBERNETES redis PV** assumes the `D:\_KUBE\data` directory exists.     
2. I used a local repository, hence the strange image names  (`127.0.0.1:5556/ordershop:product`)     
3. I used **[KOMPOSE](https://github.com/kubernetes/kompose "KOMPOSE")** hence the labels with `io.kompose....` in them 
 
 # OPTIONAL: 
 
 ##### Initially I ran Kompose to generate the yaml files for Kubernetes from the DOCKER files.

    >choco install kubernetes-kompose
    
    >kompose version
        1.18.0 (06a2e56)


###### I changed these files considerably to get this to work, add persistence, expose ports etc... 
###### I also had to change the Dockerfiles to copy the python code into the app directory. Otherwise the app dir was empty and nothing worked.      
###### Run "kompose" from root dir to create deployment files
    
    >kompose convert
    
         Kubernetes file "gateway-api-service.yaml" created
         Kubernetes file "redis-service.yaml" created
         Kubernetes file "billing-service-deployment.yaml" created
         Kubernetes file "crm-service-deployment.yaml" created
         Kubernetes file "customer-service-deployment.yaml" created
         Kubernetes file "gateway-api-deployment.yaml" created
         Kubernetes file "inventory-service-deployment.yaml" created
         Kubernetes file "msg-service-deployment.yaml" created
         Kubernetes file "order-service-deployment.yaml" created
         Kubernetes file "product-service-deployment.yaml" created
         Kubernetes file "redis-deployment.yaml" created
         
         
         
#### LOCAL DOCKER REGISTRY

#### Run a local repo        
             
         >docker run -d -p 5556:5000 --restart=always --name registry registry:2
 
 #### Push to the local repo after a build
 
    >docker-compose push
 
 #### You will see a lot of this
 
     The push refers to repository [127.0.0.1:5556/ordershop]
    12a02885dd03: Pushed
    5fb94d471980: Pushed
    9f72e27f9aa4: Pushed
    
    b17cc31e431b: Pushing [=============================================>     ]  128.9MB/141.8MB
    12cb127eee44: Pushed
    604829a174eb: Pushed
    fbb641a8b943: Pushed
 
 
 #### You images will be safely stored in a repo that can be shared with others.
