import json
import os
import sys
import boto3
from botocore.exceptions import ClientError
from time import sleep

OWNER_NAME = sys.argv[1] if len(sys.argv) >= 2 else "Tarefas_Demo"
KEY_PAIR_NAME = sys.argv[2] if len(sys.argv) >= 3 else "Tarefa_Demo_Keypair"
SEC_GROUP_NAME = sys.argv[3] if len(sys.argv) >= 4 else "Tarefas_Demo_Secgroup"
SEC_GROUP_ID = ""
INSTANCE_COUNT = sys.argv[4] if len(sys.argv) >= 5 else 3

with open('aws.json') as fd:
    cred = json.load(fd)

AWSACCESSKEYID = cred["aws_access_key_id"]
AWSSECRETACCESSKEY = cred["aws_secret_access_key"]

ec2 = boto3.client("ec2", region_name="us-east-1", aws_access_key_id=AWSACCESSKEYID, aws_secret_access_key=AWSSECRETACCESSKEY)
WAITER_TERMINATE = ec2.get_waiter('instance_terminated')
WAITER_RUNNING = ec2.get_waiter('instance_status_ok')

def delete_old_lb():
    try:
        delete_instances_ids = []
        existing_instances = ec2.describe_instances()
        running_instances = list(existing_instances.values())[0]
        for instances_group in running_instances:
            instances = instances_group["Instances"]
            for i in instances:
                if (i["State"]["Code"] == 16):
                    for t in i["Tags"]:
                        if(t["Key"] == "Owner" and t["Value"] == OWNER_NAME+"_LB"):
                            delete_instances_ids.append(i["InstanceId"])
        if (len(delete_instances_ids) > 0):
            print("Existing Load Balancer. Deleting...")
            deleted = ec2.terminate_instances(InstanceIds=delete_instances_ids)
            print("Delete response: ", deleted["ResponseMetadata"]["HTTPStatusCode"])
            print("Wait for old Load Balancer to delete. This may take a while...")
            WAITER_TERMINATE.wait(InstanceIds=delete_instances_ids)
            print("Load Balancer deleted.")
    except ClientError as e:
            print("An error occured while trying to delete Load Balancer.")
            print(e)

def create_credentials():
    global SEC_GROUP_ID
    ######### KEY PAIR #############
    try:
        print("Creating Key Pair")
        existing_kp = ec2.describe_key_pairs()
        for key in list(existing_kp.values())[0]:
            if (key["KeyName"] == KEY_PAIR_NAME):
                print("Existing key pair. Deleting...")
                deleted = ec2.delete_key_pair(KeyName=KEY_PAIR_NAME)
                os.remove("./" + KEY_PAIR_NAME + ".pem")
                print("Delete response: ", deleted["ResponseMetadata"]["HTTPStatusCode"])
        created = ec2.create_key_pair(KeyName=KEY_PAIR_NAME)
        key_file = open(KEY_PAIR_NAME + ".pem", "w")
        key_file.write(created["KeyMaterial"])
        os.chmod("./" + KEY_PAIR_NAME + ".pem", 0o400)
        print("Created new .pem file.")
        print("Create response: ", created["ResponseMetadata"]["HTTPStatusCode"])
    except ClientError as e:
            print("An error occured while trying to create a Key Pair")
            print(e)

    ######### SECURITY GROUP #############
    try:
        print("Creating Security Group")
        description = "SecGroup created by the tarefas demo. Testing purposes only."
        existing_sg = ec2.describe_security_groups()
        for sg in list(existing_sg.values())[0]:
            if (sg["GroupName"] == SEC_GROUP_NAME):
                print("Existing security group. Deleting...")
                deleted = ec2.delete_security_group(GroupName=sg["GroupName"], GroupId=sg["GroupId"])
                print("Delete response: ", deleted["ResponseMetadata"]["HTTPStatusCode"])
        response = ec2.describe_vpcs()
        vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

        response = ec2.create_security_group(GroupName=SEC_GROUP_NAME,
                                            Description=description,
                                            VpcId=vpc_id)
        print("Create response: ", created["ResponseMetadata"]["HTTPStatusCode"])
        SEC_GROUP_ID = response['GroupId']
        print('Security Group Created %s in vpc %s.' % (SEC_GROUP_ID, vpc_id))

        data = ec2.authorize_security_group_ingress(
            GroupId=SEC_GROUP_ID,
            IpPermissions=[
                {'IpProtocol': 'tcp',
                'FromPort': 80,
                'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp',
                'FromPort': 5000,
                'ToPort': 5000,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ])
        print("Authorization response: ", data["ResponseMetadata"]["HTTPStatusCode"])
    except ClientError as e:
        print("An error occured while trying to create a Security Group")
        print(e)

def launch_lb():
    try:
        deployed_instances_ids = []
        user_data = """#!/bin/bash
        sudo apt-get -y update 
        sudo apt-get install -y python3-pip
        sudo pip3 install flask
        sudo pip3 install boto3
        cd
        git clone https://github.com/filipefborba/CloudDeploy.git
        cd CloudDeploy/
        python3 load_balancer.py {0} {1} {2} {3} {4} {5}
        """.format(OWNER_NAME, KEY_PAIR_NAME, SEC_GROUP_NAME, INSTANCE_COUNT, AWSACCESSKEYID, AWSSECRETACCESSKEY)
        instance = ec2.run_instances(
            ImageId="ami-0ac019f4fcb7cb7e6", #Ubuntu 18.04
            MinCount=1, MaxCount=1,
            InstanceType="t2.micro",
            KeyName=KEY_PAIR_NAME,
            SecurityGroupIds=[SEC_GROUP_ID],
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [{"Key": "Owner","Value": OWNER_NAME+"_LB"}]
                }],
            UserData=user_data)
        print("User Data: ", user_data)
        print("Load Balancer creation response: \n", instance)
        print("Wait while Load Balancer is created. This may take a moment...")
        deployed_instances = list(instance.values())[1]
        for i in deployed_instances:
            deployed_instances_ids.append(i["InstanceId"])
        WAITER_RUNNING.wait(InstanceIds=deployed_instances_ids)
        print("Load Balance created. Warmup sleeping for a while...")
        sleep(20)
    except ClientError as e:
        print("An error occured while trying to create a Load Balancer")
        print(e)

def get_lb_ip():
    try:
        existing_instances = ec2.describe_instances()
        running_instances = list(existing_instances.values())[0]
        for instances_group in running_instances:
            instances = instances_group["Instances"]
            for i in instances:
                if (i["State"]["Code"] == 16):
                    for t in i["Tags"]:
                        if(t["Key"] == "Owner" and t["Value"] == OWNER_NAME+"_LB"):
                            print("Load Balancer: ", i["PublicIpAddress"])
                            return i["PublicIpAddress"]
    except ClientError as e:
            print("An error occured while trying to list the instances.")
            print(e)

def main():
    delete_old_lb()
    create_credentials()
    launch_lb()
    get_lb_ip()

main()
