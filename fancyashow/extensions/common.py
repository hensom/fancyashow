import logging
import re
from copy               import deepcopy

logger = logging.getLogger(__name__)

RESOURCE_HANDLED         = 0
RESOURCE_HANDLING_FAILED = 1
RESOURCE_NOT_HANDLED     = 2

class ResourceExtractor(object):
  def resources(self, node):
    raise NotImplementedError()
    
class ResourceExtractorManager(object):
  def __init__(self, extractors):
    self.extractors = [e() for e in extractors]

  def extract_resources(self, *nodes):
    resources = { }

    for node in nodes:
      if node is None:
        continue

      for extractor in self.extractors:
        for uri in extractor.resources(node):
          resources[uri] = True

    return resources.keys()
    
class Processor(object):
  def __init__(self, library, settings):
    self.library  = library
    self.settings = settings

  @classmethod
  def default_state(self):
    return { }

  def clone_state(self, state):
    return deepcopy(state)

  def process(self, o, state, dependent_states):
    raise NotImplementedError()

  def cleanup(self, o, state):
    raise NotImplementedError()

  def get_required_setting(self, settings, name):
    try:
      return settings[name]
    except KeyError:
      raise Exception('%s is a required setting for processor: %s' % (name, self.id()))

  @classmethod    
  def id(self):
    raise NotImplementedError()

  @classmethod
  def depends_on(self):
    raise NotImplementedError()