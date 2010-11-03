class Festival(object):
  def __init__(self, name, url = None):
    self.name = name
    self.url  = url

class Venue(object):
  def __init__(self, name, url = None):
    self.name          = name
    self.url           = url

class Show(object):
  def __init__(self):
    self.merge_key    = None
    self.title        = None
    self.performers   = []
    self.date         = None
    self.door_time    = None
    self.show_time    = None
    self.soldout      = False
    self.free         = False
    self.venue        = None
    self.festival     = None
    self.resources    = ShowResources()
    
class ShowResources(object):
  def __init__(self):
    self.image_url     = None
    self.show_url      = None
    self.resource_uris = []

class Performer(object):
  def __init__(self, name, headliner = False, start_time = None):
    self.name         = name
    self.headliner    = headliner
    self.start_time   = start_time
    self.resources    = PerformerResources()
    
  def __str__(self):
    return self.name
    
class PerformerResources(object):
  def __init__(self):
    self.site_url  = None
