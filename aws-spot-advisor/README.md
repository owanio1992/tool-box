# describe
this tool help get spot information, incloud price,frequency of interruption
the frequency of interruption data is come from  
https://aws.amazon.com/ec2/spot/instance-advisor/


# prerequisite

## Amazon EC2 Instance Selector
https://github.com/aws/amazon-ec2-instance-selector

```
os=$(uname | tr 'A-Z' 'a-z')
arch=$(printf "%s" "$(uname -m | tr 'A-Z' 'a-z' | sed -E 's/x86_64|i[3-6]86/amd64/;s/aarch64|arm64/arm64/')")
curl -Lo ec2-instance-selector https://github.com/aws/amazon-ec2-instance-selector/releases/latest/download/ec2-instance-selector-$os-$arch && chmod +x ec2-instance-selector
./ec2-instance-selector --version

```

## uv
https://github.com/astral-sh/uv


# config
please update `config.py` ec2_instance_selector_args  
arg ref.
```
./ec2-instance-selector --help
```

use env as source https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html

# execute 
```
uv run python3 main.py
```


# sample output

```

Region: ap-northeast-1 (Tokyo)
+-----------------+---------+-------------+------------+-----------------+--------------------------+--------------------------+
| Instance Type   |   VCPUs |   Mem (GiB) | CPU Arch   | Spot Price/Hr   |   Savings over On-Demand | Interruption Frequency   |
+=================+=========+=============+============+=================+==========================+==========================+
| i4i.large       |       2 |          16 | x86_64     | $0.0725         |                       67 | 5-10%                    |
+-----------------+---------+-------------+------------+-----------------+--------------------------+--------------------------+

Region: eu-west-1 (Ireland)
+-----------------+---------+-------------+------------+-----------------+--------------------------+--------------------------+
| Instance Type   |   VCPUs |   Mem (GiB) | CPU Arch   | Spot Price/Hr   |   Savings over On-Demand | Interruption Frequency   |
+=================+=========+=============+============+=================+==========================+==========================+
| i4i.large       |       2 |          16 | x86_64     | $0.0854         |                       55 | 10-15%                   |
+-----------------+---------+-------------+------------+-----------------+--------------------------+--------------------------+

Region: ap-southeast-2 (Sydney)
+-----------------+---------+-------------+------------+-----------------+--------------------------+--------------------------+
| Instance Type   |   VCPUs |   Mem (GiB) | CPU Arch   | Spot Price/Hr   |   Savings over On-Demand | Interruption Frequency   |
+=================+=========+=============+============+=================+==========================+==========================+
| i4i.large       |       2 |          16 | x86_64     | $0.0609         |                       72 | 5-10%                    |
+-----------------+---------+-------------+------------+-----------------+--------------------------+--------------------------+

```