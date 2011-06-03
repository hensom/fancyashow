import                                    logging
from datetime                      import datetime

from tastypie.fields               import CharField, ApiField, RelatedField, DateField
from tastypie.authentication       import Authentication
from tastypie.authorization        import Authorization
from tastypie.resources            import ApiField, Resource
from tastypie.exceptions           import ImmediateHttpResponse
from tastypie.http                 import HttpBadRequest
from tastypie.utils                import trailing_slash
from tastypie.utils.mime           import determine_format, build_content_type

from mangopie.resources            import DocumentResource
from mangopie.fields               import ListField, EmbeddedResourceField

from django.conf.urls.defaults     import url
from django.core.urlresolvers      import reverse 

from fancyashow.db.models          import Show, ArtistInfo
from fancyashow.ui.fancy_api.forms import SavedShowsForm
from fancyashow.ui.fancy_main.auth import User

LOG = logging.getLogger(__name__)

class CurrentVisitorAuthentication(Authentication):
  def is_authenticated(self, request, **kwargs):
    return request.user.is_authenticated()

class CurrentVisitorAuthorization(Authorization):
  def is_authorized(self, request, object = None):
    return request.user.is_authenticated()

class SparseArtistResource(DocumentResource):
  class Meta:
    object_class = ArtistInfo
    fields       = ['name', 'start_time']
    
class ShowUrlField(ApiField):
  def dehydrate(self, bundle):
    show = bundle.obj

    kwargs = {
      'venue':  show.venue.slug(),
      'year':   show.date.year,
      'month':  show.date.month,
      'day':    show.date.day,
      'artist': show.slug()
    }
    
    return reverse('show-details', kwargs = kwargs)
    
class ShowImageField(ApiField):
  def dehydrate(self, bundle):
    show = bundle.obj
    return show.images.get('featured', {}).get('url')

class ShowResource(DocumentResource):
  artists = ListField(EmbeddedResourceField(SparseArtistResource), attribute = 'artists')
  url     = ShowUrlField()
  image   = ShowImageField()

  class Meta:
    object_class = Show
    fields       = ['id', 'title', 'artists', 'date', 'show_time', 'door_time', 'soldout', 'venue', 'rank']
    
class ShowListField(ApiField):
  def dehydrate(self, bundle):
    show_ids = bundle.obj.starred_show_set.show_ids
    shows    = []

    if show_ids:
      shows = list(Show.objects.filter(id__in = show_ids).order_by('date'))

    show_resource = ShowResource()
    
    return [show_resource.full_dehydrate(s) for s in shows]

class VisitorResource(DocumentResource):
  saved_shows = ShowListField('saved_shows')
  
  def get_object_list(self, request):
    queryset = super(VisitorResource, self).get_object_list(request)

    return queryset.filter(username = request.user.username)
    
  def obj_get(self, request = None, **kwargs):
    return self.get_object_list(request).get()

  def dispatch_saved_shows(self, request, **kwargs):
    return self.dispatch('saved_shows', request, **kwargs)

  def post_saved_shows(self, request, **kwargs):
    LOG.debug('in saved show')
    form = SavedShowsForm(request.POST)

    if form.is_valid():
      user        = request.user
      add, remove = form.cleaned_data['add'], form.cleaned_data['remove']

      LOG.debug('Request by user: %s to add: %s, remove: %s' % (user, add, remove))
      
      show_set = user.starred_show_set

      if add and add.id:
        show_set.add_shows([add])

      if remove and remove.id:
        show_set.remove_shows([remove])

      if add or remove:
        show_set.save()
    else:
      desired_format = self.determine_format(request)
      serialized     = self.serialize(request, form.errors, desired_format)
      response       = HttpBadRequest(content=serialized, content_type=build_content_type(desired_format))

      raise ImmediateHttpResponse(response=response)
  
  def override_urls(self):
    return [
        url(r"^(?P<resource_name>%s)%s$"             % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail')),
        url(r"^(?P<resource_name>%s)/saved_shows%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_saved_shows'))
    ]

  class Meta:
    resource_name  = 'me'
    saved_shows_allowed_methods = ['post']
    authentication = CurrentVisitorAuthentication()
    authorization  = CurrentVisitorAuthorization()
    object_class   = User
    fields         = ['first_name', 'last_name', 'id']
