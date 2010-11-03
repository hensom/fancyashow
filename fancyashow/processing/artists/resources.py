from fancyashow.extensions        import ExtensionLibrary, ArtistProcessor
from fancyashow.processing.common import ResourceHandlerProcessorMixin

extensions = ExtensionLibrary()

class ArtistResourceHandler(ResourceHandlerProcessorMixin, ArtistProcessor):
  def resources(self, obj, state, dependent_states):
    resources = { }
    
    for key, profile_state in dependent_states.get('profile-parser', {}).iteritems():
      for uri in profile_state['resources']:
        resources[uri] = True
        
    return resources.keys()
    
  def handlers(self):
    return [h() for h in self.library.artist_resource_handlers()]
    
  @classmethod
  def id(self):
    return 'resource-handler'
    
  @classmethod
  def depends_on(self):
    return ('profile-parser', )
    
extensions.register_artist_processor(ArtistResourceHandler)