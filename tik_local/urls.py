from django.conf.urls import url
from router.views import PhoneView, redirect_req

urlpatterns = [
    url(r"^phone/$", PhoneView.as_view(), name='phone'),
    url(r'^.*/$', redirect_req, name='home'),
    url(r'^$', redirect_req),

]
