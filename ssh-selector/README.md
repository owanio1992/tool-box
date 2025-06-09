usage  
`python3 aws_instance.py <service> command`  

**service**
allow `service1`, `service2` ...  

**command**
allow  
    `update`  : fetch instance info, save to local  
    `<site>`  : select site to connect  

## site
`python3 aws_instance.py connect <service> <site> [filter str]`

**site**

more detail please see `service_site` in config.py

eg.
```
python3 aws_instance.py service1 a
```
