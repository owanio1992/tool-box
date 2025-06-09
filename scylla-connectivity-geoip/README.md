
```
# add SG allow NAT access scylla

# install auto update geoip DB to server
./deploy.sh <site> geolite none --limit=<>

# create virtualenv 
cd /opt/nebula/venv
virtualenv geoip_helper
cd geoip_helper

# copy "main.py", "requirements.txt" to server
source bin/activate && pip3 install -r requirements.txt

# copy "geoip_helper.service" to /etc/systemd/system/geoip_helper.service
# update `Environment`
sudo systemctl daemon-reload
sudo systemctl start geoip_helper
sudo systemctl enable geoip_helper



# deploy fluent-bit 
./deploy.sh <site> fluent-bit none --limit=<>
```
