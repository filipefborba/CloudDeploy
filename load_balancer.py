from flask import Flask, Response, redirect
from threading import Timer, Thread
from time import sleep
from botocore.exceptions import ClientError
import boto3
import requests
import json
import os
import sys

# OWNER_NAME = "Tarefas_LB"
# KEY_PAIR_NAME = "Tarefa_Demo_Keypair"
# SEC_GROUP_NAME = "Tarefas_Demo_Secgroup"
# INSTANCE_COUNT = 3

OWNER_NAME = sys.argv[1]
KEY_PAIR_NAME = sys.argv[2]
SEC_GROUP_NAME = sys.argv[3]
SEC_GROUP_ID = ""
INSTANCE_COUNT = int(sys.argv[4])
AWSACCESSKEYID = sys.argv[5]
AWSSECRETACCESSKEY = sys.argv[6]

ec2 = boto3.client("ec2", region_name="us-east-1", aws_access_key_id=AWSACCESSKEYID, aws_secret_access_key=AWSSECRETACCESSKEY)
WAITER_TERMINATE = ec2.get_waiter('instance_terminated')
WAITER_RUNNING = ec2.get_waiter('instance_status_ok')

AVAILABLE_INSTANCES = {}
INSTANCES_IPS = list(AVAILABLE_INSTANCES.values())
REGISTERED_INSTANCES = 1
REQUEST_COUNT = 0

def get_instances():
    global SEC_GROUP_ID
    try:
        existing_instances = ec2.describe_instances()
        running_instances = list(existing_instances.values())[0]
        for instances_group in running_instances:
            instances = instances_group["Instances"]
            for i in instances:
                if (i["State"]["Code"] == 16):
                    for t in i["Tags"]:
                        if(t["Key"] == "Owner" and t["Value"] == OWNER_NAME):
                            AVAILABLE_INSTANCES[i["InstanceId"]] = i["PublicIpAddress"]
                    for g in i["SecurityGroups"]:
                        if(g["GroupName"] == SEC_GROUP_NAME):
                            SEC_GROUP_ID = g["GroupId"]

    except ClientError as e:
            print("An error occured while trying to list the instances.")
            print(e)

def recreate_intances(shutdown_id):
    print("Terminating instance: " + str(shutdown_id))
    try:
        deleted = ec2.terminate_instances(InstanceIds=[shutdown_id])
        print("Delete response: ", deleted["ResponseMetadata"]["HTTPStatusCode"])
        WAITER_TERMINATE.wait(InstanceIds=[shutdown_id])
        print("Instance deleted.")
    except ClientError as e:
            print("An error occured while trying to delete instance.")
            print(e)

    try:
        instance = ec2.run_instances(
            ImageId="ami-0ac019f4fcb7cb7e6", #Ubuntu 18.04
            MinCount=1, MaxCount=1,
            InstanceType="t2.micro",
            KeyName=KEY_PAIR_NAME,
            SecurityGroupIds=[],
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [{"Key": "Owner","Value": OWNER_NAME}]
                }],
            UserData=
            """#!/bin/bash
            cd
            git clone https://github.com/filipefborba/CloudDeploy.git
            cd CloudDeploy/
            source setup_app
            """)
        print("Instance creation response: \n", instance)
        print("Wait while instance is created. This may take a moment...")
        running_id = instance["Instances"][0]["InstanceId"]
        WAITER_RUNNING.wait(InstanceIds=[running_id])
        print("Instance created. Warmup sleeping for a while...")
        sleep(10)
        get_instances()
    except ClientError as e:
        print("An error occured while trying to create an Instance")
        print(e)

def init():
    if not AVAILABLE_INSTANCES:
        ######### CREATE INSTANCES #############
        try:
            deployed_instances_ids = []
            instance = ec2.run_instances(
                ImageId="ami-0ac019f4fcb7cb7e6", #Ubuntu 18.04
                MinCount=INSTANCE_COUNT, MaxCount=INSTANCE_COUNT,
                InstanceType="t2.micro",
                KeyName=KEY_PAIR_NAME,
                SecurityGroupIds=[SEC_GROUP_ID],
                TagSpecifications=[{
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Owner","Value": OWNER_NAME}]
                    }],
                UserData=
                """#!/bin/bash
                cd
                git clone https://github.com/filipefborba/CloudDeploy.git
                cd CloudDeploy/
                source setup_app
                """)
            print("Instance creation response: \n", instance)
            print("Wait while instance is created. This may take a moment...")
            deployed_instances = list(instance.values())[1]
            for i in deployed_instances:
                deployed_instances_ids.append(i["InstanceId"])
            WAITER_RUNNING.wait(InstanceIds=deployed_instances_ids)
            print("Instance created. Warmup sleeping for a while...")
            sleep(20)
        except ClientError as e:
            print("An error occured while trying to create an Instance")
            print(e)
    else:
        print("Instances available. Not running 'init' ")

### THREADING ###
def health_checker():
    global INSTANCES_IPS, REGISTERED_INSTANCES 
    INSTANCES_IPS = list(AVAILABLE_INSTANCES.values())
    REGISTERED_INSTANCES = len(INSTANCES_IPS)
    for ip in INSTANCES_IPS:
        try:
            r = requests.get("http://" + ip + ":5000/healthcheck", timeout=5)
            print(ip + ": " + str(r.status_code))
        except:
            print(ip, "failed")
            for id, instance_ip in AVAILABLE_INSTANCES.items():
                if ip == instance_ip:
                    shutdown_id = id
            AVAILABLE_INSTANCES.pop(shutdown_id)
            t = Timer(30.0, health_checker).start()
            recreate_intances(shutdown_id)
    t = Timer(30.0, health_checker).start()
    

def load_balance(path):
    global REQUEST_COUNT, INSTANCES_IPS, REGISTERED_INSTANCES 
    INSTANCES_IPS = list(AVAILABLE_INSTANCES.values())
    REGISTERED_INSTANCES = len(INSTANCES_IPS)
    ip = INSTANCES_IPS[REQUEST_COUNT % REGISTERED_INSTANCES]
    REQUEST_COUNT += 1
    return redirect("http://" + ip + ":5000/" + path)

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    load = load_balance(path)
    return load

# Main
get_instances()
init()
t = Timer(30.0, health_checker)
t.start()
app.run(host=os.environ["APP_URL"], port=5000)