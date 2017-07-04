from django.core.management.base import BaseCommand
import requests
from django.utils.timezone import now
from django.conf import settings
from subprocess import Popen, PIPE
from time import sleep

iptables_cmd = \
    """sudo iptables -t nat -D PREROUTING -s %(local_ip)s -p tcp --dport 443 -j  DNAT --to-destination %(router_ip)s:443
sudo iptables -t nat -D PREROUTING -s %(local_ip)s -p tcp --dport 80 -j  DNAT --to-destination %(router_ip)s:80
sudo iptables -t nat -D PREROUTING -s %(local_ip)s -p tcp --dport 53 -j  DNAT --to-destination %(router_ip)s:8053
sudo iptables -t nat -D PREROUTING -s %(local_ip)s -p udp --dport 53 -j  DNAT --to-destination %(router_ip)s:8053
"""


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('ip', nargs='+')
        parser.add_argument('mac', nargs='+')

    def handle(self, *args, **options):
        return
        while True:
            try:
                result = requests.post('%s/api/ip/%s/' % (settings.API_HOST_URL, settings.ROUTER_DEVICE_ID,),
                                       data={'ip': options['ip'][0], 'mac': options['mac'],
                                             'ts': now().timestamp(), 'event': 'release'})
                if result.status_code == 200:
                    print(result.content)
                    break
            except Exception as e:
                print(e, type(e))
                sleep(1)
        if result.status_code == 200:
            for l in (iptables_cmd % {'local_ip': options['ip'][0], 'router_ip': settings.LAN_IP}).splitlines():
                ps = Popen(l.split(), stdout=PIPE, stderr=PIPE)
                print(ps.communicate())
                print(l)

