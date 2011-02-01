from django.conf.urls.defaults import *
from tastypie.api import Api
from fancyashow.ui.fancy_api.resources import ShowResource, VisitorResource

v1_api = Api(api_name='v1')
v1_api.register(VisitorResource())
v1_api.register(ShowResource())

urlpatterns = patterns('',
  (r'^', include(v1_api.urls))
)
