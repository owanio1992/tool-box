import time
import json
from cassandra.cluster import Cluster,DCAwareRoundRobinPolicy
from cassandra import ConsistencyLevel
import geohash
import geoip2.database
import os
import logging

logfile='/opt/nebula/log/geoip_helper.log'
geoip_file='/opt/nebula/geo/GeoLite2-City.mmdb'
logging.basicConfig(filename=logfile, level=logging.INFO,
                    format='%(message)s')

# Connect to your Scylla cluster
cluster = Cluster([
   os.getenv("SCYLLA_SERVER_1"),
   os.getenv("SCYLLA_SERVER_2",None),
   os.getenv("SCYLLA_SERVER_3",None)
                   ],load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=""))
session = cluster.connect("scylla_nebula_data")
session.default_timeout = 30
query_stmt = session.prepare("""
    SELECT * FROM t_helper_connectivity 
    WHERE epoch >= ? AND epoch < ?
    ALLOW FILTERING                                 
    """)
query_stmt.consistency_level = ConsistencyLevel.ONE

class GeoIPReader:
    _instance = None
    _reader = None
    _last_read_time = 0

    def __new__(cls, geoip_file):
        if cls._instance is None:
            cls._instance = super(GeoIPReader, cls).__new__(cls)
            cls._instance._initialize(geoip_file)
        return cls._instance

    def _initialize(self, geoip_file):
        self._reader = geoip2.database.Reader(geoip_file)
        self._last_read_time = time.time()

    def get_reader(self):
        if time.time() - self._last_read_time > 7 * 24 * 3600:
            self._reader = geoip2.database.Reader(geoip_file)
            self._last_read_time = time.time()
        return self._reader

def get_geoip_info(ipv4_address):
  reader = GeoIPReader(geoip_file).get_reader()
  try:
    response = reader.city(ipv4_address)
    geoip_city_name = response.city.names.get('en') 
    geoip_country_name = response.country.names.get('en')
    geoip_location_latitude = response.location.latitude if response.location else None
    geoip_location_longitude = response.location.longitude if response.location else None
    geohash_code = geohash.encode(geoip_location_latitude, geoip_location_longitude, precision=8)

    return {
    'city': geoip_city_name,
    'country': geoip_country_name,
    'geohash': geohash_code
    }

  except geoip2.errors.AddressNotFoundError:
    print(f"Error: IPv4 address '{ipv4_address}' not found in the GeoIP database.")
    return None

def query_helper_connectivity(start_time):
    end_time = int(time.time() * 1000)
    global time_last_query
    time_last_query = end_time
    rows = session.execute(query_stmt, [start_time,end_time])
    data_list = []
    for row in rows:
        row_dict = {
            'epoch': str(int(row.epoch.timestamp())),
            'entry_type': row.entry_type, # connect,disconnect
            'outter_ipv4': row.outter_ipv4
        }
        data_list.append(row_dict)
    return data_list
 
if __name__ == "__main__":

    time_last_query = int(time.time() * 1000) # now
    while True:
        # Clear the log file 
        with open(logfile, 'w'):
            pass
        
        connectivitys = query_helper_connectivity(time_last_query)
        for connectivity in connectivitys:
           connectivity.update(get_geoip_info(connectivity.get("outter_ipv4")))
           logging.info(json.dumps(connectivity))

        time.sleep(60)
