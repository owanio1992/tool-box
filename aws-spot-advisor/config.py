# use ENV as credencial source
# https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html

# will loop all region to get data
aws_region = {
    "ap-northeast-1": "Tokyo",
    "eu-west-1": "Ireland",
    "ap-southeast-2": "Sydney",
    "ap-east-2": "Taipei",
}

ec2_instance_selector_args = {
    "memory-min": "16 GiB", # Minimum Amount of Memory available (Example: 4 GiB) If --memory-max is not specified, the upper bound will be infinity
    "memory-max": "128 GB", # Maximum Amount of Memory available (Example: 4 GiB) If --memory-min is not specified, the lower bound will be 0
    "vcpus-min": 2, # Minimum Number of vcpus available to the instance type. If --vcpus-max is not specified, the upper bound will be infinity
    "vcpus-max": 2, # Maximum Number of vcpus available to the instance type. If --vcpus-min is not specified, the lower bound will be 0
    "price-per-hour-max": 1.6, # Maximum Price/hour in USD (Example: 0.09) If --price-per-hour-min is not specified, the lower bound will be 0
    "cpu-architecture": "amd64",  # allow [x86_64, amd64, x86_64_mac, i386, arm64, or arm64_mac]
    "allow-list": "i4i.large", # List of allowed instance types to select from w/ regex syntax (Example: m[3-5]\.*)
}

# don't change unless you know what are you doing
ec2_instance_selector_common_args = {
    "usage-class": "spot", # Usage class: [spot or on-demand]
    "max-results": 512,
    "output": "table-wide",
    "sort-by": ".SpotPrice",
}

# Columns to display in the output table
output_columns = [
    "Instance Type",
    "VCPUs",
    "Mem (GiB)",
    "CPU Arch",
    "Spot Price/Hr",
    "Savings over On-Demand",
    "Interruption Frequency",
]
