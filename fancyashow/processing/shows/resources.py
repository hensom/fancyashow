from fancyashow.extensions        import ExtensionLibrary, ShowProcessor
from fancyashow.processing.common import ResourceHandlerProcessorMixin

extensions = ExtensionLibrary()

class ShowResourceHandlerProcessor(ResourceHandlerProcessorMixin, ShowProcessor):
  def resources(self, obj, state, dependent_states):
    return obj.parsed_resources
    
  def handlers(self):
    return [h() for h in self.library.show_resource_handlers()]
    
  @classmethod
  def id(self):
    return 'resource-handler'
    
  @classmethod
  def depends_on(self):
    return ( )
    
extensions.register_show_processor(ShowResourceHandlerProcessor)