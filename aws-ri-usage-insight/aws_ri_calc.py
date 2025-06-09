import boto3
import sys
import csv
import time
import yaml
from typing import TypedDict
from tabulate import tabulate

def instance_calc():

    instances_infos = []
    class instances_infos_type(TypedDict):
        instance_name: str
        instance_type: str
        instance_size: str
        instance_type_all: str
        instance_size_fp: float

    session = boto3.Session(
        region_name = aws_info["region"],
        profile_name = aws_info["profile"],
    )
    client = session.client("ec2")

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    describe_instances = client.describe_instances(
        Filters = [
            {
                'Name': "instance-state-name",
                'Values': ["running"],
            },
        ],
    )

    for aws_instances in describe_instances["Reservations"]:
        for instances_info in aws_instances["Instances"]:

            # skip spot 
            if instances_info.get("InstanceLifecycle") is not None:
                continue

            # convert Tags to dictionary
            tags = {tag["Key"]: tag["Value"] for tag in instances_info["Tags"]}
            
            # if name not exist, use ip
            if tags.get("Name") is None:
                tags["Name"] = instances_info["PrivateIpAddress"]

            # split instance type
            instance_type_split = instances_info.get("InstanceType").split(".")

            instance_type = instance_type_split[0]
            instance_size = instance_type_split[1]
            instance_size_fp = instance_size_footprint(instance_size)

            temp = {}
            temp: instances_infos_type = {
                "instance_type_all": instances_info.get("InstanceType"), 
                "instance_name": tags["Name"], 
                "instance_type": instance_type, 
                "instance_size": instance_size, 
                "instance_size_fp": instance_size_fp,
            }
            instances_infos.append(temp)

    instance_fp = {}
    for instances_info in instances_infos:

        # inital dictionary
        if instance_fp.get(instances_info["instance_type"]) is None:
            instance_fp[instances_info["instance_type"]] = 0

        instance_fp[instances_info["instance_type"]] += instances_info["instance_size_fp"]
    
    # dump instance data
    with open(f'{time_now}_{aws_info["region"]}_aws_type_calc_instances_dump.yml', "w") as f_instances_infos:
        yaml.dump(instances_infos, f_instances_infos)

    return instance_fp



def instance_size_footprint(size):
    # RI instance size footprint
    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ri-modifying.html#ri-modification-instancemove

    for k, v in ri_factor.items():
        if size == k:
            ret = v

    return ret

def ri_calc():

    ri_infos = []

    class ri_infos_type(TypedDict):
        ri_type: str
        ri_size: str
        ri_size_fp: float


    session = boto3.Session(
        region_name = aws_info["region"],
        profile_name = aws_info["profile"],
    )
    client = session.client("ec2")

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
    describe_reserved_instances = client.describe_reserved_instances(
        Filters = [
            {
                "Name": "state",
                "Values": ["active"]
            },
        ],
    )

    for aws_ri in describe_reserved_instances["ReservedInstances"]:

        # split ri type
        ri_type_split = aws_ri.get("InstanceType").split(".")

        ri_type = ri_type_split[0]
        ri_size = ri_type_split[1]
        ri_count = aws_ri["InstanceCount"]
        ri_size_fp = (instance_size_footprint(ri_size) * ri_count)
        
        temp = {}
        temp: ri_infos_type = {
            "ri_type": ri_type, 
            "ri_size": ri_size, 
            "ri_size_fp": ri_size_fp,
        }

        ri_infos.append(temp)

    ri_fp = {}
    for ri_info in ri_infos:
        # inital dictionary
        ri_fp.setdefault(ri_info["ri_type"],0)

        ri_fp[ri_info["ri_type"]] += ri_info["ri_size_fp"]

    return ri_fp

def output_csv(instance, ri):

    output_row = [
        [f"timestamp: {time_now}", f"region: {aws_info['region']}"],
        ["#############################","#######################"],
        ["instance type", "instance size footprint", "RI type", "RI size footprint", "RI utilization quota (RI FP - instance FP)"]
    ]

    # write instance first 
    for k, v in instance.items():
        output_row.append([f"{k}", f"{v}", f"{k}", f"{ri.get(k, 0)}", f"{ri.get(k, 0)-v}"])
        ri.pop(k,"")

    # write not used ri
    for k, v in ri.items():
        output_row.append(["", "", k, ri.get(k, 0), ri.get(k, 0)])

    # append separate line
    output_row.append([""])
    output_row.append(["#############################","#######################"])
    output_row.append(["RI factor referance: ","https://ppt.cc/fd0ZRx"])
    output_row.append(["#############################","#######################"])

    # fp referance 
    output_row.append(["Instance size", "Normalization factor"])

    for k, v in ri_factor.items():
        output_row.append([k, v])

    print(tabulate(output_row))

    with open(f'{time_now}_{aws_info["region"]}_aws_type_calc.csv', "w", newline = "") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(output_row)




ri_factor = {
    "nano": 0.25,
    "micro": 0.5,
    "small": 1,
    "medium": 2,
    "large": 4,
    "xlarge": 8,
    "2xlarge": 16,
    "3xlarge": 24,
    "4xlarge": 32,
    "6xlarge": 48,
    "8xlarge": 64,
    "9xlarge": 72,
    "10xlarge": 80,
    "12xlarge": 96,
    "16xlarge": 128,
    "18xlarge": 144,
    "24xlarge": 192,
    "32xlarge": 256,
    "56xlarge": 448,
    "112xlarge": 896,
}

try:
    if "tokyo" == sys.argv[1]:
        aws_info = {
            "region": "ap-northeast-1",
            "profile": "alpha3_ci"
        }


    elif "ireland" == sys.argv[1]:
        aws_info = {
            "region": "eu-west-1",
            "profile": "<fill me>"
        }

    else:
        raise

    # start here
    time_now = time.strftime("%Y-%m-%dT%H%M%SZ")
    instance = instance_calc()
    ri = ri_calc()
    output_csv(instance,ri)
    print("footprint: normalization factor of the instance size and the number of instances")
    print("==============================================================")
    print("complete, manual upload csv,yml to")
    print("https://myppt.cc/w6v6Ju")

except:
    print("""# error: no region input or error region
# usage:
# in ci server exec
pyenv activate venv_3.10.4
python3 aws_ri_calc.py ireland
# or
python3 aws_ri_calc.py tokyo""")

    exit(1)

