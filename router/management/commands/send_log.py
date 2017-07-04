from django.core.management.base import BaseCommand
import requests
import os
import shutil
from django.conf import settings
import gzip
from time import sleep


class Command(BaseCommand):
    def handle(self, *args, **options):
        src_dir = '/var/log'
        dst_dir = '/tmp/'
        for f in os.listdir(src_dir):
            if not f.startswith('iptables.log'):
                continue
            print(f)
            shutil.copy(os.path.join(src_dir, f), os.path.join(dst_dir, f))
            arch = os.path.join(dst_dir, f)
            with open(arch, 'rb') as f_in:
                with gzip.open(os.path.join(dst_dir, f) + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            while True:
                try:
                    res = requests.post('%s/api/log/%s/' % (settings.API_HOST_URL, settings.ROUTER_DEVICE_ID,),
                                        files={'file': open(arch, 'rb')})
                    print(res.status_code)
                    break
                except:
                    sleep(1)