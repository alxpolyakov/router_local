from .forms import CodeForm, PhoneForm
from django.http import HttpResponse
from django.views.generic import FormView
import base64
from django.conf import settings


class PhoneView(FormView):
    template_name = 'phone_form.html'

    def get_form_kwargs(self):
        # kwargs = super(PhoneView, self.get_form_kwargs())
        kwargs = {'request': self.request}
        if 'phone' in self.request.session:
            kwargs['phone'] = self.request.session['phone']
        if self.request.POST:
            kwargs['data'] = self.request.POST
        # elif self.request.session.get('phone', None) is not None:
        #     kwargs['data'] = {'phone': self.request.session.get('phone', None).lstrip('+')}
        else:
            kwargs['data'] = None
        return kwargs

    def get_form_class(self):
        if 'phone' in self.request.session:
            return CodeForm
        return PhoneForm

    def form_valid(self, form):
        form.save()
        return super(PhoneView, self).form_valid(form)

    def get_success_url(self):
        if self.request.session.get('phone_confirmed', False):
            try:
                url = base64.b64decode(self.request.GET.get('next', None))
            except:
                url = settings.DEFAULT_HOME_URL
            return url
        return self.request.build_absolute_uri()


def redirect_req(request):
    if not settings.LAN_PORT == 80 and not settings.LAN_PORT == 443:
        port_suffix = ':%s' % (settings.LAN_PORT,)
    else:
        port_suffix = ''
    _proto = 'https' if request.META['SERVER_PROTOCOL'].startswith('https') else 'http'
    _to = '%s://%s%s/phone/?next=%s' % (_proto, settings.ROUTER_HOST, port_suffix, base64.b64encode(
        request.build_absolute_uri().encode()).decode(),)
    resp = HttpResponse(status=511, content="""
    <html>
  <head>
    <title>Network Authentication Required</title>
    <meta http-equiv="refresh" content="5; url=%(to)s">
    
  </head>
  <body>
    <p>You need to <a href="%(to)s">
    authenticate with the local network</a> in order to gain
    access.</p>
  </body>
</html>
    """ % {'to': _to}, content_type="text/html")

    return resp


"""
iptables -I INPUT 1 -s  
"""