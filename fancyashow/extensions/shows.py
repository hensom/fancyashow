from fancyashow.extensions.common import Processor

class ShowParser(object):
  def __init__(self, settings, resource_extractor):
    self.settings           = settings
    self.resource_extractor = resource_extractor

  def __iter__(self):
    return self

  def next(self):
    raise NotImplementedError()

  @classmethod    
  def id(self):
    raise NotImplementedError()
    
class ShowProcessor(Processor):
  pass

class ShowResourceHandler(object):
  def supports(self, uri):
    raise NotImplementedError()

  def handle(self, show, uri):
    raise NotImplementedError()

  @classmethod
  def id(self):
    raise NotImplementedError()