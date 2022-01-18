#!/usr/bin/env python

from sys import argv

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI

import time
import os

class SingleSwitchWithNHostsTopo( Topo ):
  def build( self, n=3 ):
    switch = self.addSwitch('s1')
    for h in range(n):
      print('h%s' % (h + 1))
      host = self.addHost('h%s' % (h + 1))
      self.addLink(host, switch, bw=1, loss=0)

def generateICMPTraffic(net):
  h1 = net.get('h1')
  h3 = net.get('h3')
  h1_IP = str(h1.IP())

  print('Traffic capture incoming...')

  h3.cmd('tcpdump -i %s "icmp[0] == 8" -w ./pcap/attack.pcap &' % h3.intfNames()[0])

  print('DOS client...')
  h3.cmd('ping %s &' % h1_IP)

  time.sleep(10)

  h3.cmd('killall ping')
  h3.cmd('killall tcpdump')
  print('Attack traffic captured.')

def runRegularTraffic(net):
  h1 = net.get('h1')
  h2 = net.get('h2')
  h1.cmd('iperf -s &')
  h2.cmd('iperf -c 10.0.0.1 -t 100 &')

def runAttackTraffic(net):
  h1 = net.get('h1')
  h3 = net.get('h3')
  print('Commencing attack...')
  h3.cmd('tcpreplay -i %s -t -l 10000 ./pcap/attack.pcap &' % h3.intfNames()[0])

  time.sleep(20)

  h3.cmd('killall tcpreplay')
  print('End of attack.')

def toggleCapture(net, stop = False):
  h1 = net.get('h1')
  h2 = net.get('h2')
  h3 = net.get('h3')
  
  if stop == True:
    print('Stop final commands.')
    h1.cmd('killall tcpdump')
    h2.cmd('killall tcpdump')
    h3.cmd('killall tcpdump')
    h1.cmd('killall iperf')
    h2.cmd('killall iperf')
  else:
    print('Start final commands...')
    h1.cmd('tcpdump -i %s -w ./pcap/h1.pcap &' % h1.intfNames()[0])
    h2.cmd('tcpdump -i %s -w ./pcap/h2.pcap &' % h2.intfNames()[0])
    h3.cmd('tcpdump -i %s -w ./pcap/h3.pcap &' % h3.intfNames()[0])

def start():
  print('Creating topology...')
  topo = SingleSwitchWithNHostsTopo()
  net = Mininet( topo=topo,
                 host=CPULimitedHost, link=TCLink,
                 autoStaticArp=True )
  net.start()

  h1 = net.get('h1')
  h2 = net.get('h2')
  h3 = net.get('h3')

  if(len(h1.intfNames()) <= 0 or len(h2.intfNames()) <= 0 or len(h3.intfNames()) <= 0):
    print('Weird, empty interface list')
    return

  generateICMPTraffic(net)
  toggleCapture(net)
  runRegularTraffic(net)
  time.sleep(10)
  runAttackTraffic(net)
  time.sleep(20)
  toggleCapture(net, True)
  net.stop()
  print('Net stop!')

def preparePcapFolder():
  os.system('rm -rf pcap')
  os.system('mkdir pcap')
  os.system('touch ./pcap/h1.pcap')
  os.system('touch ./pcap/h2.pcap')
  os.system('touch ./pcap/h3.pcap')
  os.system('touch ./pcap/attack.pcap')

if __name__ == '__main__':
  setLogLevel( 'info' )
  preparePcapFolder()
  start()
