# OVERVIEW:

This is my attempt to take the master branch in the ordershop repo and run it on KUBERNETES.
It uses Replica Sets, Persistent Volumes, and Services to make this scalable.

I hope this will eventually server as an archetype for a KUBERNETES based microservice architecture.

Unfortunately this app currently has some problems. See [Problems](#problems)  

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

###### Note I did all my development on Docker Desktop Community  

    Version 2.0.0.3 (31259)
    Channel: stable
    Build: 8858db3 

##### I deployed to the "docker-for-desktop" cluster in the "default" namespace. You might make your own cluster and namespace and change the yaml files accordingly.
         
#### Apply all the yaml files in the root dir.
###### Note the `error validating "docker-compose.yml"` error is expected

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
 
 ![Alt text](./dashboard.png?raw=true "KUBERNETES DASHBOARD")
 
 ##### Steps to run from KUBERNETES (run from the project root directory)
    
1. Install dependencies by `pip3 install -r client/requirements.txt`.

2. Execute the client by `python -m unittest client/client.py`.   #or py -3  

There should be no failures ..... but alas there are 4

    ======================================================================
    FAIL: test_5_update_second_order (client.client.OrderShopTestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "D:\_KUBE\ordershop\client\client.py", line 236, in test_5_update_second_order
        self.assertEqual(orders[1]['product_ids'][0], order['product_ids'][0])
    AssertionError: 'd81f86de-8f39-4655-86c4-7585172bd188' != 'b5976a36-2a87-4591-8463-bb0232800631'
    - d81f86de-8f39-4655-86c4-7585172bd188
    + b5976a36-2a87-4591-8463-bb0232800631
    
    
    ======================================================================
    FAIL: test_6_delete_third_order (client.client.OrderShopTestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "D:\_KUBE\ordershop\client\client.py", line 252, in test_6_delete_third_order
        self.assertIsNone(json.loads(rsp))
    AssertionError: {'id': 'c7d21a05-27be-4992-aac0-bffe8fe182e0', 'product_ids': ['e6559ddd-b8ac-4204-aae1-211ee85416e6', '377efd25-a624-4795-8cd6-8d8118b35c91', '753910ef-7356-4530-bfcf-4f13e0d14056', 'f5320e6c-4390-42dd-813b-073293ee283e', 'd81f86de-8f39-4655-86c4-7585172bd188', 'd81f86de-8f39-4655-86c4-7585172bd188', 'ef1a939d-c5a6-44c1-ac4f-a94840066fb7'], 'customer_id': '34ee3702-ce3b-4e34-82f3-ed2fa2f5862c'} is not None
    
    ======================================================================
    FAIL: test_7_delete_third_customer (client.client.OrderShopTestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "D:\_KUBE\ordershop\client\client.py", line 268, in test_7_delete_third_customer
        self.assertIsNone(json.loads(rsp))
    AssertionError: {'id': '34ee3702-ce3b-4e34-82f3-ed2fa2f5862c', 'name': 'Nwuwmeinuc', 'email': 'nwuwmeinuc@server.com'} is not None
    
    ======================================================================
    FAIL: test_9_get_unbilled_orders (client.client.OrderShopTestCase)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "D:\_KUBE\ordershop\client\client.py", line 292, in test_9_get_unbilled_orders
        self.assertEqual(len(unbilled), 8)
    AssertionError: 9 != 8
    
    ----------------------------------------------------------------------
    Ran 10 tests in 0.939s
    
    FAILED (failures=4)       
      
 # PROBLEMS:
 
 I have looked at this and I am baffled.
 In KUBERNETES can see the redis data exists and is persisted ie. POST works. 
 
 But DELETE and PUT are not working.
 
 It has to be something simple, but I have not found it.
    
      
# NOTES:

The DOCKER version of redis is not persistent, but the KUBERNETES version is.

There are a few assumptions. 

1. KUBERNETES redis assumes `D:\_KUBE\data` exists. It is used for the redis persistence volume       
2. I used a local repository, hence the strange image names  (`127.0.0.1:5556/ordershop:product`)     
3. I used KOMPOSE hence the labels with `io.kompose....` in them 
 
 # OPTIONAL: 
 
 ##### Initially I ran Kompose to generate the yaml files for Kubernetes from the DOCKER files.

    >choco install kubernetes-kompose
    
    >kompose version
        1.18.0 (06a2e56)


###### I changed these files considerably to get this to work, add persistence, expose ports etc... 
###### I also had to change the Dockerfiles to copy the python code into the app directory. Otherwise the app dir was empty and nothing worked.      
###### Run "kompose" from root dir with Docker Compose file to create deployment files
    
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
         
         
         
### LOCAL DOCKER REGISTRY

#### Run a local repo        
             
         >docker run -d -p 5556:5000 --restart=always --name registry registry:2
 
 #### Push to the local repo after a build
 
    >docker-compose push
 
 #### You will see a lot of this
 
     The push refers to repository [127.0.0.1:5556/ordershop]
    eb85d3dd1ece: Pushed
    8736c8cd4bc6: Pushed
    bd55ae8b39fe: Pushed
    476ad49bd5e1: Pushed
    97a14a7f4413: Pushed
    8d42e8813996: Pushed
    b579820b7f4b: Pushed
    e86b9ff68e49: Pushed
    846a554a833e: Pushed
    7b5b713a60af: Pushed
    12a02885dd03: Pushed
    5fb94d471980: Pushed
    9f72e27f9aa4: Pushed
    
    b17cc31e431b: Pushing [=============================================>     ]  128.9MB/141.8MB
    12cb127eee44: Pushed
    604829a174eb: Pushed
    fbb641a8b943: Pushed
 
 
 #### You images are safely stored in a repo that can be shared with others.
