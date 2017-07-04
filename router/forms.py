from django import forms
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget
from django.utils.translation import ugettext_lazy as _
import requests
from django.conf import settings
from .utils import ArpCache
from django.utils.timezone import now
import json
from subprocess import Popen, PIPE
from django.core.cache import cache


class PhoneForm(forms.Form):
    _req = None
    phone = PhoneNumberField(max_length=16, label=_('Phone number'), widget=PhoneNumberInternationalFallbackWidget)

    def __init__(self, *args, **kwargs):
        self._req = kwargs.pop('request', None)
        return super(PhoneForm, self).__init__(*args, **kwargs)

    def save(self):
        api_url = '%s/api/phone/%s/' % (settings.API_HOST_URL, settings.ROUTER_DEVICE_ID,)
        c = ArpCache()
        req = requests.post(api_url, data={'number': str(self.cleaned_data['phone']),
                                           'ip': self._req.META['REMOTE_ADDR'],
                                           'mac': c.get_mac(self._req.META['REMOTE_ADDR']),
                                           'ts': now().timestamp(), 'task': 'register'})
        d = json.loads(req.content.decode())
        if cache.get('phones') is None:
            cache.set('phones', {})
        storing_phones = cache.get('phones')
        storing_phones[c.get_mac(self._req.META['REMOTE_ADDR'])] = {'code': d['code'], 'phone_id': d['id'],
                                                                    'phone': str(self.cleaned_data['phone']),
                                                                    'assigned': False}
        cache.set('phones', storing_phones)
        self._req.session['code'] = d['code']
        self._req.session['phone_id'] = d['id']
        self._req.session['phone'] = str(self.cleaned_data['phone'])


iptables_cmd = \
    """/usr/bin/sudo /sbin/iptables -t nat -D PREROUTING -s %(local_ip)s -p tcp --dport 443 \
-j DNAT --to-destination %(router_lan_ip)s:%(router_https_port)s
/usr/bin/sudo /sbin/iptables -t nat -D PREROUTING -s %(local_ip)s -p tcp --dport 80 \
-j DNAT --to-destination %(router_lan_ip)s:%(router_http_port)s
/usr/bin/sudo /sbin/iptables -t nat -D PREROUTING -s %(local_ip)s -p tcp --dport 53 \
-j DNAT --to-destination %(router_lan_ip)s:8053
/usr/bin/sudo /sbin/iptables -t nat -D PREROUTING -s %(local_ip)s -p udp --dport 53 \
-j DNAT --to-destination %(router_lan_ip)s:8053
/usr/bin/sudo /sbin/iptables -t nat -A PREROUTING -s %(local_ip)s -p tcp --dport 53 \
-j DNAT --to-destination %(router_lan_ip)s
/usr/bin/sudo /sbin/iptables -t nat -A PREROUTING -s %(local_ip)s -p udp --dport 53 \
-j DNAT --to-destination %(router_lan_ip)s
/usr/bin/sudo /sbin/iptables -t nat -A POSTROUTING -s %(local_ip)s -p tcp ! --dport 53 -j MASQUERADE
/usr/bin/sudo /sbin/iptables -t nat -A POSTROUTING -s %(local_ip)s -p udp ! --dport 53 -j MASQUERADE
"""


class CodeForm(forms.Form):
    phone = PhoneNumberField(widget=forms.TextInput(attrs={'readonly': True}))
    code = forms.CharField(max_length=10, label=_('Code'))

    def __init__(self, *args, **kwargs):
        self._req = kwargs.pop('request', None)
        phone = kwargs.pop('phone', '')
        super(CodeForm, self).__init__(*args, **kwargs)
        self.fields['phone'].initial = phone.lstrip('+')

    def clean_code(self):
        c = self.cleaned_data['code']
        if not self._req.session['code'] == c:
            raise forms.ValidationError(_('Incorrect code'))
        return c

    def save(self):
        c = ArpCache()
        api_url = '%s/api/phone/%s/' % (settings.API_HOST_URL, settings.ROUTER_DEVICE_ID,)
        req = requests.post(api_url, data={'id': self._req.session['phone_id'],
                                           'ip': self._req.META['REMOTE_ADDR'],
                                           'mac': c.get_mac(self._req.META['REMOTE_ADDR']),
                                           'ts': now().timestamp(), 'task': 'assign'})

        if req.status_code == 200:
            d = json.loads(req.content.decode())
            if d['result'] == 'ok':
                for x in ['code', 'phone_id', 'phone']:
                    del self._req.session[x]
                for l in (iptables_cmd % {'local_ip': self._req.META['REMOTE_ADDR'], 'router_wan_ip': settings.WAN_IP,
                                          'router_lan_ip': settings.LAN_IP,
                                          'router_https_port': settings.ROUTER_HTTPS_PORT,
                                          'router_http_port': settings.ROUTER_HTTP_PORT}).splitlines():

                    out = Popen(l.split(), stderr=PIPE, stdout=PIPE).communicate()
                    print(l)
                    print(out)
                self._req.session['phone_confirmed'] = True
                return True

