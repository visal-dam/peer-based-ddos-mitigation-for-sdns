#PEER SUPPORT

import requests
import threading
import random

# ===== CONSTANTS =====

# Credentials to connect to ONOS controller
onos_ip = "172.17.0.2"
usr = "onos"
pwd = "rocks"
rest_port = 8181

# Maximum capacity of switch and threshold beyond which the strategy takes place
max = 4000
threshold = 3000

# Other
t = '' #threading constant, needed for threads

# ===== MONITORING LOGIC =====

# gets the current number of flow rules in a switch AND a each flow details
def get_switch_flows(switch_id):
    url = f"http://{onos_ip}:{rest_port}/onos/v1/flows/{switch_id}"
    response = requests.get(url, auth=(usr, pwd))
    flow_stats = response.json()
    flow_count = len(flow_stats['flows'])
    return flow_count, flow_stats['flows']

# returns two lists of peers, idle and full, determined by current number of flow rules
def find_peers():
    device_ids = []
    idle_peers_list = []
    full_peers_list = []
    idle_flows = {}

    #gets_devices():
    url = f"http://{onos_ip}:{rest_port}/onos/v1/devices"
    response = requests.get(url, auth=(usr, pwd))
    devices = response.json()['devices']
    for i in range(0, len(devices)):
        device_ids.append(devices[i]['id'])

    # checks eligibility, appends to list of potential peers
    for switch in device_ids:
        count, stats = get_switch_flows(switch)
        if count < threshold:
            idle_peers_list.append(switch)
            idle_flows[switch] = stats
        else:
            full_peers_list.append(switch)
    return idle_peers_list, full_peers_list, idle_flows

# gets current link information between switches
def get_links():
    url = f"http://{onos_ip}:{rest_port}/onos/v1/links"
    response = requests.get(url, auth=(usr, pwd))
    return response.json()["links"]

# processes link information, returns the port that connects A and B from A; eg: S1:2 --> S2:1 returns 2
def get_ports(links, s, d):
    ports = []
    for link in links:
        if link['src']['device'] == s and link['dst']['device'] == d:
            ports.append(int(link['src']['port']))
    if len(ports) != 0:
        return ports[random.randint(0, len(ports)-1)]
    else:
        return "FAIL"

# ===== TRAFFIC GUIDING LOGIC =====

# (threading) installs a wildcard flow rule targeted towards to ipv4 packets
def traffic_guider(source_id, s_to_d_port):  # ports must be string, invoked when > threshold
    catch_all_rule_source = \
        {
            "priority": 39999, #lower than 40000 which is lldp
            "timeout": 0,  #in seconds
            "isPermanent": True,
            "deviceId": source_id,
            "state": "ADDED",
            "treatment": {
                "instructions": [
                    {
                        "type": "OUTPUT",
                        "port": s_to_d_port
                    },

                ]
            },
            "selector": {
                "criteria": [
                    #normally, criteria would be empty, expressed as [], but we cannot forward lldp packets which would invalidate links
                ]

            }
        }
    url_post_s = f"http://{onos_ip}:{rest_port}/onos/v1/flows/{source_id}"
    threading.Thread(target=tg_post_s, args=(url_post_s, catch_all_rule_source)).start() #does it in a separate thread so it does not need to wait for a response from the controller

# target function posts the flow rule above
def tg_post_s(url_post_s, catch_all_rule_source):
    requests.post(url_post_s, json=catch_all_rule_source, auth=(usr, pwd))

# (threading) deletes any catch-all rule in a switch when it goes back below threshold such that traffic can be processed as normal
def del_catch_all(device_id, idle_flows):  #invoked when < threshold
    flows = idle_flows.get(device_id)
    for flow in flows:
        if flow['priority'] == 39999:
            flow_id = flow['id']
            url = f"http://{onos_ip}:{rest_port}/onos/v1/flows/{device_id}/{flow_id}"
            threading.Thread(target=tg_del, args=(url, t)).start()
            break

# target function to delete catch-all rules
def tg_del(url, t):
    requests.delete(url=url, auth=(usr, pwd))

# ===== PEER SUPPORT FUNCTION =====
def peer_support():
    while True:
        idle, full, idle_flows = find_peers()
        links = get_links()

        if len(full) != 0:  #i.e., > theshold
            for f in full:
                if len(idle) != 0:
                    i = random.randint(0, len(idle)-1)
                    s_to_d = get_ports(links, f, idle[i])
                    print(f, ' --> ', idle[i], '(Port: ', s_to_d, ')')
                    idle.pop(i)
                    traffic_guider(f, s_to_d)

        for i in idle:  #for when full becomes idle, permananent rule is deleted
            del_catch_all(i, idle_flows)


# ===== MAIN =====
peer_support()

