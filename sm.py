#MONITORING SCRIPT

import requests
import time
import random
from time import sleep

onos_ip = "172.17.0.2"
usr = "onos"
pwd = "rocks"
rest_port = 8181

stats = {}

def get_switch_flow_count(switch_id):
    url = f"http://{onos_ip}:{rest_port}/onos/v1/flows/{switch_id}"
    response = requests.get(url, auth=(usr, pwd))

    flow_stats = response.json()
    flow_count = len(flow_stats['flows'])
    stats[switch_id].append(str(flow_count)) #for stats
    return flow_count

def get_switch_flow(switch_id):
    url = f"http://{onos_ip}:{rest_port}/onos/v1/flows/{switch_id}"
    response = requests.get(url, auth=(usr, pwd))
    flow_stats = response.json()
    return flow_stats['flows']

def init_stats():
    url = f"http://{onos_ip}:{rest_port}/onos/v1/devices"
    response = requests.get(url, auth=(usr, pwd))
    devices = response.json()['devices']
    device_ids = []
    for i in range (0, len(devices)):
        device_ids.append(devices[i]['id'])

    for device in device_ids:
        stats[device] = []

def print_stats():
    print("Printing stats...")
    peers = current_dev
    filename = str(random.randint(0,10000000000000000))
    with open(filename+".txt", 'x') as file:
        for i in range(0, len(peers)):
            file.write("FLOW STATS FOR SWITCH " + str(peers[i]) + "\n")
            file.write('\n'.join(stats[peers[i]]) + '\n')

def find_all_peers():
    device_ids = []

    #gets ids of all current switches
    url = f"http://{onos_ip}:{rest_port}/onos/v1/devices"
    response = requests.get(url, auth=(usr, pwd))
    try:
        devices = response.json()['devices']
        for i in range (0, len(devices)):
            device_ids.append(devices[i]['id'])
        return device_ids
    except():
        return 1

def fail(source_id): #drops all packets = spike drop
    failed = \
        {
            "priority": 50000, #high priority
            "timeout": 0,  #in seconds
            "isPermanent": True,
            "deviceId": source_id,
            "state": "ADDED",
            "treatment": {
                "instructions": [

                ]
            },
            "selector": {
                "criteria": [
                    #normally, criteria would be empty, expressed as [], but we cannot forward lldp packets which would invalidate links
                ]

            }
        }
    url = f"http://{onos_ip}:{rest_port}/onos/v1/flows/{source_id}"
    print(requests.post(url, json=failed, auth=(usr, pwd)))

current_dev = find_all_peers()

for d in current_dev:
    flows = get_switch_flow(d)
    for flow in flows:
        if flow['priority'] == 50000:
            flow_id = flow['id']
            url = f"http://{onos_ip}:{rest_port}/onos/v1/flows/{d}/{flow_id}"
            requests.delete(url=url, auth=(usr, pwd))


init_stats()
lost = False
start = time.time()
while time.time() - start <= 300:
    for dev in current_dev:
        if get_switch_flow_count(dev) > 4000:
            fail(dev)
    sleep(1)
print(time.time() - start)
print_stats()