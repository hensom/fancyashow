class ParserError(Exception):
  def __init__(self, url, html, *args, **kwargs):
    super(ParserError, self).__init__(*args, **kwargs)

    self.url  = url
    self.html = html
    
class ShowParser(object):
  def __init__(self, resource_extractor):
    self.resource_extractor = resource_extractor

  def __iter__(self):
    return self

  def next(self):
    raise NotImplementedError()

  @classmethod    
  def id(self):
    raise NotImplementedError()
    
class ProfileParser(object):
  def parse(self, artist, profile):
    raise NotImplementedError()
    
  @classmethod
  def id(self):
    raise NotImplementedError()
    