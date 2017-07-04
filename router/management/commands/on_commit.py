from django.core.management.base import BaseCommand
import requests
from django.utils.timezone import now
from django.conf import settings
from subprocess import Popen, PIPE
from time import sleep
from django.core.cache import cache

iptables_cmd = \
    """sudo iptables -t nat D POSTROUTING -s %(local_ip)s ! --dport 53 -j MASQUERADE
/usr/bin/sudo /sbin/iptables -t nat -D POSTROUTING -s %(local_ip)s -p tcp ! --dport 53 -j MASQUERADE
/usr/bin/sudo /sbin/iptables -t nat -D POSTROUTING -s %(local_ip)s -p udp ! --dport 53 -j MASQUERADE
/usr/bin/sudo /sbin/iptables -t nat -D PREROUTING -s %(local_ip)s -p tcp --dport 53 -j DNAT --to-destination %(router_lan_ip)s
/usr/bin/sudo /sbin/iptables -t nat -D PREROUTING -s %(local_ip)s -p udp --dport 53 -j DNAT --to-destination %(router_lan_ip)s
sudo iptables -t nat -A PREROUTING -s %(local_ip)s -p tcp --dport 443 -j  DNAT --to-destination %(router_lan_ip)s:%(router_https_port)s
sudo iptables -t nat -A PREROUTING -s %(local_ip)s -p tcp --dport 80 -j  DNAT --to-destination %(router_lan_ip)s:%(router_http_port)s
sudo iptables -t nat -A PREROUTING -s %(local_ip)s -p tcp --dport 53 -j  DNAT --to-destination %(router_lan_ip)s:8053
sudo iptables -t nat -A PREROUTING -s %(local_ip)s -p udp --dport 53 -j  DNAT --to-destination %(router_lan_ip)s:8053

"""


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('ip', nargs='+')
        parser.add_argument('mac', nargs='+')

    def handle(self, *args, **options):
        mac = options['mac'][0]
        storing_phones = cache.get('phones')
        if mac in storing_phones:
            return
        while True:
            try:
                result = requests.post('%s/api/ip/%s/' % (settings.API_HOST_URL, settings.ROUTER_DEVICE_ID,),
                                       data={'ip': options['ip'][0], 'mac': mac,
                                             'ts': now().timestamp(), 'event': 'commit'})
                if result.status_code == 200:
                    break
            except Exception as e:
                print(e, type(e))
                sleep(1)
        if result.status_code == 200:
            out = Popen('sudo iptables -t nat -L'.split(), stdout=PIPE, stderr=PIPE).communicate()[0].decode()
            apply_rules = True
            for l in out.splitlines():
                if l.split() == ['DNAT', 'tcp', '--', options['ip'][0], 'anywhere', 'tcp',
                                 'dpt:https', 'to:%s:%s' % (settings.LAN_IP, settings.ROUTER_HTTPS_PORT)]:
                    apply_rules = False
                    break
            if apply_rules:
                for l in (iptables_cmd % {'local_ip': options['ip'][0], 'router_wan_ip': settings.WAN_IP,
                                          'router_lan_ip': settings.LAN_IP,
                                          'router_https_port': settings.ROUTER_HTTPS_PORT,
                                          'router_http_port': settings.ROUTER_HTTP_PORT}).splitlines():
                    print(Popen(l.split(), stdout=PIPE, stderr=PIPE).communicate())


"""
iptables -I OUTPUT 1 -j LOG --log-prefix="[iptables_packets]" --log-level 1
"""