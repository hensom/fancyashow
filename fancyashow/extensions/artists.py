from fancyashow.extensions.common import Processor

class ArtistProcessor(Processor):
  pass

class ArtistProfileParserResult(object):
  def __init__(self, resources):
    self.resources = resources

class ArtistProfileParser(object):
  def __init__(self, resource_extractor):
    self.resource_extractor = resource_extractor

  def supports(self, profile):
    raise NotImplementedError()

  def parse(self, artist, profile):
    raise NotImplementedError()
    
  @classmethod
  def id(self):
    raise NotImplementedError()
    
class ArtistMediaExtractor(object):
  def extract_media(self, artist):
    return []

  @classmethod
  def id(cls):
    raise NotImplementedError()
    
class ArtistResourceHandler(object):
  def supports(self, uri):
    raise NotImplementedError()

  def handle(self, artist, uri):
    raise NotImplementedError()

  @classmethod
  def id(self):
    raise NotImplementedError()