from mininet.topo import Topo
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch

class CustomOVSSwitch(OVSSwitch):
    def __init__(self, name, **kwargs):
        super(CustomOVSSwitch, self).__init__(name, protocols='OpenFlow13', **kwargs)
class MeshTopo(Topo):
    def build(self):
        ss = [self.addSwitch('s{}'.format(i+1)) for i in range(10)]

        for i in range(10):
            for j in range(i + 1, 10):
                self.addLink(ss[i], ss[j])

        for i in range(len(ss)):
            #for j in range(2):  # Create 2 hosts per switch
            host = self.addHost('h{}'.format(i-1))  # Unique host names
            self.addLink(host, ss[i])  # Link host to the switch

topos = {'mesh' : MeshTopo}

if __name__ == '__main__':
    topo = topos['mesh']()

    c = RemoteController('c0', ip='172.17.0.2', port=6653)
    #s = OVSSwitch('s23', protocols='OpenFlow13')

    net = Mininet(topo=topo, controller=c, switch=CustomOVSSwitch)

    net.start()

    CLI(net)
    net.stop()