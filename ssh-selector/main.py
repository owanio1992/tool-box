import os
import boto3
import yaml
import sys
import re
from typing import TypedDict
from config import *
import logging
import logging.config

logging.basicConfig(level="INFO",
                    format='%(asctime)s %(levelname)-8s %(name)s %(message)s')
logger = logging.getLogger(__name__)
# import pprint
# pp = pprint.PrettyPrinter(indent=4)


def update_inventory():

    # define aws profile
    # zyxel
    try:
        aws_infos = aws_profiles[SERVICE]
        logger.info(f"update {SERVICE} inventory: start")
    except:
        logger.error(f"{SERVICE} not exist")

    # sample instance info structure
    class instances_infos_type(TypedDict):
        instance_region: str
        instance_ip: str
        instance_name: str
        instance_key: str

    instances_infos = []

    # list of name to find which instanse use public ip
    str_pubip = ["NAT"]

    output_lines = ["declare -A connection=( \n"]

    # get all sites instance
    for aws_info in aws_infos:
        session = boto3.Session(
            region_name=aws_info["region"],
            profile_name=aws_info["profile"],
        )
        
        logger.info(f"update {SERVICE} inventory, region: {aws_info['region']}")

        client = session.client('ec2')
        describe_instances = client.describe_instances()
        # read instance info

        for aws_instances in describe_instances["Reservations"]:
            for instances_info in aws_instances["Instances"]:

                # convert Tags to dictionary
                tags = {}
                if instances_info.get("Tags"):
                    for tag in instances_info["Tags"]:
                        tags.update({tag["Key"]: tag["Value"]})
                else:
                    tags.update({"Tags": "is not exist"})

                # if name not exist, use ip
                if not tags.get("Name"):
                    tags["Name"] = instances_info["PrivateIpAddress"]

                instance_region = aws_info.get("region")
                instance_ip = instances_info.get("PrivateIpAddress")
                instance_pub_ip = instances_info.get("PublicIpAddress")
                instance_name = tags.get("Name").replace(" ", "")
                instance_key = instances_info.get("KeyName")

                # if name in prefix_pubip, change instance ip to use public ip, default use private ip
                if any(prefix in instance_name for prefix in str_pubip):
                    instance_ip = instance_pub_ip

                temp: instances_infos_type = {
                    "instance_region": instance_region,
                    "instance_ip": instance_ip,
                    "instance_name": instance_name,
                    "instance_key": instance_key,
                }
                instances_infos.append(temp)

                # wirte connection info
                output_lines.append(
                    f'["{instance_name}"]="ssh ubuntu@{instance_ip}" \n'
                    # f'["{instance_name}"]="ssh -i /data/ssh_key/{instance_key}.pem ubuntu@{instance_ip}" \n'
                )

                # group instances by site
                instance_site = "other"  # as default site
                break_out_flag = False
                for site_key, site_value in SITES.items():
                    if site_key != "other":
                        for prefix in site_value.get("prefix"):
                            if instance_name.startswith(prefix):
                                instance_site = site_key
                                break_out_flag = True
                                break
                    elif break_out_flag == False:  # not match, instance in other site
                        break_out_flag = True
                    if break_out_flag == True:
                        SITES[instance_site]["instance"].append(
                            {
                                "instance_region": instance_region,
                                "instance_ip": instance_ip,
                                "instance_name": instance_name,
                                "instance_key": instance_key,
                            }
                        )
                        break  # write only once
    output_lines.append(")\n")
    with open(f"{WORK_DIR}/{SERVICE}_instances_connection_info.sh", "w") as sh_file:
        sh_file.writelines(output_lines)

    # sort instance, for user-friendly
    for k, v in SITES.items():
        v["instance"] = sorted(
            v["instance"], key=lambda instance: instance["instance_name"])

    with open(f"{WORK_DIR}/{SERVICE}_instances_sites.yml", "w") as f_sites:
        yaml.dump(SITES, f_sites)

    logger.info(f"update {SERVICE} inventory: done")
    
    # generate connect.sh
    output_lines = []
    output_lines.append(
        "#!/bin/bash\n" +
        "HEIGHT=45\n" +
        "WIDTH=60\n" +
        "CHOICE_HEIGHT=45\n" +
        "BACKTITLE=\"ssh connector\"\n" +
        "TITLE=\"ssh connector\"\n" +
        "MENU=\"Choose one of the following options:\"\n" +
        f"source ~/ssh_selector/{SERVICE}_instances_connection_info.sh\n" +
        f"source ~/ssh_selector/{SERVICE}_instances_connection_menu.sh\n" +
        "CHOICE=$(dialog --clear \\\n" +
        "                --backtitle \"$BACKTITLE\" \\\n" +
        "                --title \"$TITLE\" \\\n" +
        "                --menu \"$MENU\" \\\n" +
        "                $HEIGHT $WIDTH $CHOICE_HEIGHT \\\n" +
        "                \"${options[@]}\" \\\n" +
        "                2>&1 >/dev/tty)\n" +
        "echo ${options[$CHOICE*2+1]}\n" +
        "eval \"${connection[${options[$CHOICE*2+1]}]}\"\n" +
        "\n"
    )
    with open(f"{WORK_DIR}/{SERVICE}_connect.sh", "w") as sh_file:
        sh_file.writelines(output_lines)


def read_inventory(site_name, filter_str):

    # read instances
    with open(f"{WORK_DIR}/{SERVICE}_instances_sites.yml", "r") as f_sites:
        sites = yaml.safe_load(f_sites)

    # generate menu list
    output_lines = [f"options=( \n"]
    list_id = 0
    for instance_info in sites[site_name]["instance"]:
        instance_name = instance_info["instance_name"]
        # instance_ip = instance_info["instance_ip"]
        # instance_key = instance_info["instance_key"]

        # 3: filter feature, else load all site's instance
        if filter_str:
            if re.search(filter_str, instance_name, re.IGNORECASE):
                output_lines.append(f"{list_id} {instance_name}\n")
                list_id += 1
            else:
                logger.error(f"filter by '{filter_str}' fail")
        else:
            output_lines.append(f"{list_id} {instance_name}\n")
            list_id += 1

    output_lines.append(")\n")
    with open(f"{WORK_DIR}/{SERVICE}_instances_connection_menu.sh", "w") as sh_file:
        sh_file.writelines(output_lines)

    # exec connect.sh
    os.system(f"bash {WORK_DIR}/{SERVICE}_connect.sh")


if __name__ == "__main__":

    WORK_DIR = os.path.dirname(os.path.abspath(__file__))
    
    if len(sys.argv) <= 2:
        with open(f"{WORK_DIR}/README.md", "r") as README:
            print(README.read())
        exit(1)
        
    SERVICE = sys.argv[1]
    # service all site
    SITES = service_site[SERVICE]

        
    if "update" == sys.argv[2]:
        update_inventory()
    else:
        for k, v in SITES.items():
            if sys.argv[2] == v["short_name"]:
                site_name = k

        filter_str = ""
        if len(sys.argv) == 4:
            filter_str=sys.argv[-1]

        read_inventory(site_name, filter_str)
