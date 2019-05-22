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

There should be no failures 
      
    
      
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




## To stop and start a pod

    kubectl scale --replicas=0 deployment/<your-pod>

    kubectl scale --replicas=1 deployment/<your-pod>



## Added this to all deployments

https://github.com/xing/kubernetes-deployment-restart-controller
https://github.com/xing/kubernetes-deployment-restart-controller#runtime-metrics


## Deploy versioning
http://kubernetesbyexample.com/deployments/







      
      
         
         
         
Run your deployments

    kubectl create configmap redis-data --from-file config/  # you might have to delete it

    kubectl apply -f .   # better but reports errors on docker compose files --- no big deal

    kubectl apply -f gateway-api-service.yaml,redis-service.yaml,billing-service-deployment.yaml,crm-service-deployment.yaml,customer-service-deployment.yaml,gateway-api-deployment.yaml,inventory-service-deployment.yaml,msg-service-deployment.yaml,order-service-deployment.yaml,product-service-deployment.yaml,redis-deployment.yaml,billing-service-service.yaml,crm-service-service.yaml,customer-service-service.yaml,gateway-api-service.yaml,inventory-service-service.yaml,msg-service-service.yaml,order-service-service.yaml,product-service-service.yaml,redis-service.yaml
    
    
Expose redis

    kubectl port-forward deployment/redis 6379:6379        
        
Check deployment    
    
    npm install -g redis-cli

Usage
    
    rdcli
    127.0.0.1:6379> ping
    PONG
    127.0.0.1:6379>   
    
    
    
## Docker - Kubectl stuff


CMD: kill all containers

    FOR /f "tokens=*" %i IN ('docker ps -q') DO docker stop %i

    FOR /f "tokens=*" %i IN ('docker ps -q') DO docker rm %i


Powershell

    docker ps -q | % { docker stop $_ }

    docker ps -q | % { docker stop $_ }

Wheres my config

    set KUBECONFIG=C:\Users\shermes641\.kube\config

Add dashboard

    kubectl create serviceaccount cluster-admin-dashboard-sa
    kubectl create clusterrolebinding cluster-admin-dashboard-sa --clusterrole=cluster-admin --serviceaccount=default:cluster-admin-dashboard-sa

    kubectl -n kube-system get secret
    kubectl describe secret cluster-admin-dashboard-sa-token-nzvph

        https://www.makeuseof.com/tag/install-pip-for-python/  gp.py    

PASTE TOKEN in dashboard signin
    
    eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImNsdXN0ZXItYWRtaW4tZGFzaGJvYXJkLXNhLXRva2VuLW56dnBoIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImNsdXN0ZXItYWRtaW4tZGFzaGJvYXJkLXNhIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiNGU2YTFjNTMtNjQ4ZC0xMWU5LWI5NzAtMDAxNTVkZjYxNTA5Iiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OmRlZmF1bHQ6Y2x1c3Rlci1hZG1pbi1kYXNoYm9hcmQtc2EifQ.tELK0FvNDJdpUZBkhgR9PyAaJOb432K3TSpVvNUI4K1yCmmhGAASPS2yH1RFoPvl5ik0doqLD4C0ziy7WeeW5OhxsoUeY5tlt6X_pl2XD6Gl6Rj7PszsCAi75UriWvin5PDCuU7yzNQ3WZy-4hAuTGYi8mcDxmFRDYsGclLv3hONBHhhFDOE9Gy3wDo411V8igHTb_dR2-WkTVbl48w9cJPPF-uw29AgpGcpEaSOsL1ohOr5UiugJFOZrpHdYl0t7zegwf4DKy4HbJagMpVc1ntYCEM1HM1Nqkd1_vTDyXyM0Tv_j_HPDRQK_P55kAsrh5F_oJSin18XjLPSU5iSbw

    kubectl proxy

    http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/

kubectl exec test-7967fb7848-6h2lt -- curl --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt -H  "Authorization: Bearer " http://10.96.0.1

kubectl exec test-7967fb7848-6h2lt -- curl --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt -H  "Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tdHZmNWYiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjUzZGQ4ZWQwLTRiMzQtMTFlOS05YWI2LTAwMTU1ZGY2MTUwOSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.kOehTX9-Az7h9dLLSq25PxBl5IZI4Toy3lXdBpIob0_mf_T7aP3p12knk3IIaIfqE6fGHOErD8u_61xIjNStbZrb-CEjeLezJTL71SqaWRIOheC6-FKpcJVAZtaDr7rf5C8HM-MgBNGvcvijuw-ZzM2dXW2fKCeUdQGz1sE1zkd-fmq--9ivOYzW2xydAtr2PKwPsoVijV5L7ISdda0dE0pYp3KYD_FtlLn__A8k3wMrQAnAPcRDGlXNdACc-CbEm6jnm4Dh6Cps72Eopwu03Lg4uMH8Fz66j6PRDnH9K2OQxqtZB0DbjW_zP9DNGzcpeDYqTI1P34iKiozPjMNjxQ" http://10.96.0.1


I used 
kubectl -n kube-system delete deployment tiller-deploy and 
kubectl -n kube-system delete service/tiller-deploy. Then 
helm --init worked. I was missing removing the service previously.


### Changes in source code --- Run from ordershop dir

    docker-compose build   # docker-compose build --no-cache    to build everything
    docker-compose push    # push to the local repo
    kubectl apply -f .     # apply to cluster --- you may need to delete pods, services, etc after applying to load new code
    
In one console:
   
    kubectl port-forward service/redis 6379:6379  
    
In another console:

    kubectl port-forward service/gateway-api 4444:5000 
    
In another console:
            
    py -3 -m unittest client/client.py   
            
            

https://matthewpalmer.net/kubernetes-app-developer/articles/kubernetes-ingress-guide-nginx-example.html    



kubectl port-forward deployment/redis-master 6379:6379
kubectl port-forward deployment/gateway-api 4444:5000


kubectl expose deployment redis --type=LoadBalancer --name=redis

kubectl expose deployment gateway-api --type=LoadBalancer --name=gateway-api-service --port=4444


kubectl expose deployment hit-counter-app --type=LoadBalancer --name=redis-cluster-test-service --port=5555



docker container prune     #removes all stopped containers
docker image prune         #removes all dangling images   


SSH into a Container
How do I SSH into a running container
There is a docker exec command that can be used to connect to a container that is already running.

Use docker ps to get the name of the existing container
Use the command docker exec -it <container name> /bin/bash to get a bash shell in the container
Generically, use docker exec -it <container name> <command> to execute whatever command you specify in the container.
How do I run a command in my container?
The proper way to run a command in a container is: docker-compose run <container name> <command>. For example, to get a shell into your web container you might run docker-compose run web /bin/bash

To run a series of commands, you must wrap them in a single command using a shell. For example: docker-compose run 
<name in yml> sh -c '<command 1> && <command 2> && <command 3>'

In some cases you may want to run a container that is not defined by a docker-compose.yml file, for example to test a new container configuration. Use docker run to start a new container with a given image: docker run -it <image name> <command>

The docker run command accepts command line options to specify volume mounts, environment variables, the working directory, and more.







    helm del --purge  redis
        release "redis" deleted

    D:\_KUBE\uptime99\ordershop>helm install --namespace default -n redis ./redis-enterprise
NAME:   redis
LAST DEPLOYED: Fri Apr 26 18:42:54 2019
NAMESPACE: default
STATUS: DEPLOYED

RESOURCES:
==> v1/Pod(related)
NAME                                                READY  STATUS             RESTARTS  AGE
redis-redis-enterprise-controller-549ffd84bd-kjb4h  0/1    ContainerCreating  0         1s
rediscluster-0                                      0/1    ContainerCreating  0         1s

==> v1/Secret
NAME                    TYPE    DATA  AGE
redis-redis-enterprise  Opaque  3     1s

==> v1/Service
NAME                       TYPE          CLUSTER-IP     EXTERNAL-IP  PORT(S)                        AGE
redis-redis-enterprise     ClusterIP     None           <none>       9443/TCP,8001/TCP              1s
redis-redis-enterprise-ui  LoadBalancer  10.111.80.226  localhost    8443:31849/TCP,9443:32567/TCP  1s

==> v1/ServiceAccount
NAME   SECRETS  AGE
redis  1        1s

==> v1beta1/Deployment
NAME                               READY  UP-TO-DATE  AVAILABLE  AGE
redis-redis-enterprise-controller  0/1    1           0          1s

==> v1beta1/PodDisruptionBudget
NAME                    MIN AVAILABLE  MAX UNAVAILABLE  ALLOWED DISRUPTIONS  AGE
redis-redis-enterprise  N/A            1                0                    1s

==> v1beta1/Role
NAME                    AGE
redis-redis-enterprise  1s

==> v1beta1/RoleBinding
NAME                    AGE
redis-redis-enterprise  1s

==> v1beta1/StatefulSet
NAME          READY  AGE
rediscluster  0/3    1s


NOTES:
Thank you for using redis enterprise.

Web UI:
=======

export POD_NAME=$(kubectl get pods --namespace default -l "app=redis-enterprise,release=redis" -o jsonpath="{.items[0].metadata.name}")
kubectl port-forward --namespace default $POD_NAME 8443


##################################################
install redis 5


https://linuxhint.com/install_redis_ubuntu/
https://github.com/antirez/redis/archive/5.0.4.tar.gz

https://serverfault.com/questions/389997/how-to-override-update-a-symlink

# 51256242b1ae is the container ID
docker commit 51256242b1ae redis-5.0


netstat -tulpn | grep LISTEN

nmap -sT -O localhost

A note about Windows users
You can check port usage from Windows operating system using following command:
netstat -bano | more
netstat -bano | grep LISTENING
netstat -bano | findstr /R /C:"[LISTEING]"











REPOSITORY                                                       TAG                 IMAGE ID            CREATED              SIZE
127.0.0.1:5556/ordershop                                         billing             c12c53fce6f4        4 seconds ago        942MB
127.0.0.1:5556/ordershop                                         crm                 1b4a3f9334a7        29 seconds ago       937MB
127.0.0.1:5556/ordershop                                         customer            af30428f41c2        46 seconds ago       942MB
127.0.0.1:5556/ordershop                                         gateway             a135f11a2f33        About a minute ago   942MB
127.0.0.1:5556/ordershop                                         inventory           7bb5c87362de        About a minute ago   942MB
127.0.0.1:5556/ordershop                                         order               47fd5ec96501        About a minute ago   942MB
127.0.0.1:5556/ordershop                                         product             ef1b167a04c0        2 minutes ago        942MB
127.0.0.1:5556/ordershop                                         msg                 1c97aa050299        2 minutes ago        942MB
ordershop_billing-service                                        latest              e828181d9de9        10 minutes ago       942MB
ordershop_crm-service                                            latest              3eeb49f95ed4        10 minutes ago       937MB
ordershop_customer-service                                       latest              a392f4826964        10 minutes ago       942MB
ordershop_gateway-api                                            latest              9ee245e35362        10 minutes ago       942MB
ordershop_inventory-service                                      latest              abbe7604f832        10 minutes ago       942MB
ordershop_order-service                                          latest              3080471f93b0        10 minutes ago       942MB
ordershop_product-service                                        latest              9ccf993111a9        10 minutes ago       942MB
ordershop_msg-service                                            latest              d4ea7684d5ef        10 minutes ago       942MB


REPOSITORY                                                       TAG                 IMAGE ID            CREATED              SIZE
127.0.0.1:5556/ordershop                                         billing             c12c53fce6f4        30 seconds ago       942MB
127.0.0.1:5556/ordershop                                         crm                 1b4a3f9334a7        55 seconds ago       937MB
127.0.0.1:5556/ordershop                                         customer            af30428f41c2        About a minute ago   942MB
127.0.0.1:5556/ordershop                                         gateway             a135f11a2f33        About a minute ago   942MB
127.0.0.1:5556/ordershop                                         inventory           7bb5c87362de        2 minutes ago        942MB
127.0.0.1:5556/ordershop                                         order               47fd5ec96501        2 minutes ago        942MB
127.0.0.1:5556/ordershop                                         product             ef1b167a04c0        2 minutes ago        942MB
127.0.0.1:5556/ordershop                                         msg                 1c97aa050299        3 minutes ago        942MB
ordershop_billing-service                                        latest              e828181d9de9        10 minutes ago       942MB
ordershop_crm-service                                            latest              3eeb49f95ed4        10 minutes ago       937MB
ordershop_customer-service                                       latest              a392f4826964        10 minutes ago       942MB
ordershop_gateway-api                                            latest              9ee245e35362        11 minutes ago       942MB
ordershop_inventory-service                                      latest              abbe7604f832        11 minutes ago       942MB
ordershop_order-service                                          latest              3080471f93b0        11 minutes ago       942MB
ordershop_product-service                                        latest              9ccf993111a9        11 minutes ago       942MB
ordershop_msg-service                                            latest              d4ea7684d5ef        11 minutes ago       942MB










https://rancher.com/blog/2019/deploying-redis-cluster/



# does not work on windows 
kubectl exec -it redis-cluster-0 -- redis-cli --cluster create --cluster-replicas 1 $(kubectl get pods -l app=redis-cluster -o jsonpath='{range.items[*]}{.status.podIP}:6379 ')

kubectl get pods -l app=redis-cluster -o  jsonpath={range.items[*]}{.status.podIP}:6379'
10.1.10.215:6379'10.1.10.216:6379'10.1.10.217:6379'10.1.10.218:6379'10.1.10.219:6379'10.1.10.220:6379'
kubectl exec -it redis-cluster-0 -- redis-cli --cluster create --cluster-replicas 1 10.1.11.29:6379 10.1.11.30:6379 10.1.11.31:6379 10.1.11.32:6379 10.1.11.33:6379 10.1.11.34:6379

#replace the ' with space
kubectl exec -it redis-cluster-0 -- redis-cli --cluster create --cluster-replicas 1 10.1.10.215:6379 10.1.10.216:6379 10.1.10.217:6379 10.1.10.218:6379 10.1.10.219:6379 10.1.10.220:6379



>>> Performing hash slots allocation on 6 nodes...
Master[0] -> Slots 0 - 5460
Master[1] -> Slots 5461 - 10922
Master[2] -> Slots 10923 - 16383
Adding replica 10.1.10.219:6379 to 10.1.10.215:6379
Adding replica 10.1.10.220:6379 to 10.1.10.216:6379
Adding replica 10.1.10.218:6379 to 10.1.10.217:6379
M: ef253c4f4d937daf18128b7304d0746105fbaf79 10.1.10.215:6379
   slots:[0-5460] (5461 slots) master
M: c3578132ba668fec42e210f20bafb24ebe26b39f 10.1.10.216:6379
   slots:[5461-10922] (5462 slots) master
M: 23b3e0d09c52e5ade25fd82a1cea258f21e0cf5c 10.1.10.217:6379
   slots:[10923-16383] (5461 slots) master
S: 75577c7f05e48d59ee23d693a21bfaa9cc6b6d99 10.1.10.218:6379
   replicates 23b3e0d09c52e5ade25fd82a1cea258f21e0cf5c
S: 28b0ec971a329b4a8671dddd020f4552b272e663 10.1.10.219:6379
   replicates ef253c4f4d937daf18128b7304d0746105fbaf79
S: da5fc36eade789c540a8ebc08ca71887d6579eb7 10.1.10.220:6379
   replicates c3578132ba668fec42e210f20bafb24ebe26b39f
Can I set the above configuration? (type 'yes' to accept): yes
>>> Nodes configuration updated
>>> Assign a different config epoch to each node
>>> Sending CLUSTER MEET messages to join the cluster
Waiting for the cluster to join
.....
>>> Performing Cluster Check (using node 10.1.10.215:6379)
M: ef253c4f4d937daf18128b7304d0746105fbaf79 10.1.10.215:6379
   slots:[0-5460] (5461 slots) master
   1 additional replica(s)
M: c3578132ba668fec42e210f20bafb24ebe26b39f 10.1.10.216:6379
   slots:[5461-10922] (5462 slots) master
   1 additional replica(s)
S: 75577c7f05e48d59ee23d693a21bfaa9cc6b6d99 10.1.10.218:6379
   slots: (0 slots) slave
   replicates 23b3e0d09c52e5ade25fd82a1cea258f21e0cf5c
S: 28b0ec971a329b4a8671dddd020f4552b272e663 10.1.10.219:6379
   slots: (0 slots) slave
   replicates ef253c4f4d937daf18128b7304d0746105fbaf79
M: 23b3e0d09c52e5ade25fd82a1cea258f21e0cf5c 10.1.10.217:6379
   slots:[10923-16383] (5461 slots) master
   1 additional replica(s)
S: da5fc36eade789c540a8ebc08ca71887d6579eb7 10.1.10.220:6379
   slots: (0 slots) slave
   replicates c3578132ba668fec42e210f20bafb24ebe26b39f
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-cluster
data:
  update-node.sh: |
    #!/bin/sh
    REDIS_NODES="/data/nodes.conf"
    sed -i -e "/myself/ s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}/${POD_IP}/" ${REDIS_NODES}
    exec "$@"
  redis.conf: |+
    cluster-enabled yes
    cluster-require-full-coverage no
    cluster-node-timeout 15000
    cluster-config-file /data/nodes.conf
    cluster-migration-barrier 1
    appendonly yes
    protected-mode no

