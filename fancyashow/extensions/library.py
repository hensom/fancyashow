import os
import logging

logger = logging.getLogger(__name__)

SHOW_PARSERS             = 'show_parsers'
SHOW_PROCESSOR           = 'show_processors'
RESOURCE_EXTRACTORS      = 'resource_extractors'
SHOW_RESOURCE_HANDLERS   = 'show_resource_handlers'
ARTIST_RESOURCE_HANDLERS = 'artist_resource_handlers'
MEDIA_EXTRACTORS         = 'media_extractors'
ARTIST_PROCESSORS        = 'artist_processors'
PROFILE_PARSERS          = 'profile_parsers'

EXTENSION_POINTS = (
  SHOW_PARSERS,
  SHOW_PROCESSOR,
  RESOURCE_EXTRACTORS,
  SHOW_RESOURCE_HANDLERS,
  ARTIST_RESOURCE_HANDLERS,
  MEDIA_EXTRACTORS,
  ARTIST_PROCESSORS,
  PROFILE_PARSERS
)

class ExtensionLibrary(object):
  def __init__(self):
    self._extension_data = dict((e, []) for e in EXTENSION_POINTS)
    
  def _get(self, extension_type):
    if extension_type in self._extension_data:
      return self._extension_data[extension_type]
    else:
      raise Exception('Invalid extension type: %s' % extension_type)
    
  def merge(self, library):
    for extension_type, data in self._extension_data.iteritems():
      data.extend( library._get(extension_type) )
      
  def register_show_parser(self, parser):
    self._extension_data[SHOW_PARSERS].append(parser)
    
  def show_parsers(self):
    return self._extension_data[SHOW_PARSERS]

  def register_artist_profile_parser(self, parser):
    self._extension_data[PROFILE_PARSERS].append(parser)

  def artist_profile_parsers(self):
    return self._extension_data[PROFILE_PARSERS]

  def register_show_processor(self, processor):
    self._extension_data[SHOW_PROCESSOR].append(processor)

  def show_processors(self):
    return self._extension_data[SHOW_PROCESSOR]
    
  def register_artist_processor(self, processor):
    self._extension_data[ARTIST_PROCESSORS].append(processor)

  def artist_processors(self):
    return self._extension_data[ARTIST_PROCESSORS]

  def register_resource_extractor(self, extractor):
    self._extension_data[RESOURCE_EXTRACTORS].append(extractor)

  def resource_extractors(self):
    return self._extension_data[RESOURCE_EXTRACTORS]
    
  def register_show_resource_handler(self, handler):
    self._extension_data[SHOW_RESOURCE_HANDLERS].append(handler)

  def show_resource_handlers(self):
    return self._extension_data[SHOW_RESOURCE_HANDLERS]

  def register_artist_resource_handler(self, handler):
    self._extension_data[ARTIST_RESOURCE_HANDLERS].append(handler)

  def artist_resource_handlers(self):
    return self._extension_data[ARTIST_RESOURCE_HANDLERS]

  def register_media_extractor(self, extractor):
    self._extension_data[MEDIA_EXTRACTORS].append(extractor)

  def media_extractors(self):
    return self._extension_data[MEDIA_EXTRACTORS]

class ExtensionLoader(object):
  def __init__(self, packages):
    self._packages = packages
    self._loaded   = False
    self._library  = ExtensionLibrary()

  @property
  def library(self):
    self._load_all()
    
    return self._library

  def _load_all(self):
    if self._loaded:
      return
      
    modules = []

    for package_match in self._packages:
      logger.debug('Attempting to load extension: %s' % package_match)

      module_names = []

      try:
        for package_name in self._resolve_packages(package_match):
          module = self._import(package_name)
          
          try:
            logger.debug('Adding extension points from: %s' % module.__file__)

            self._library.merge(module.extensions)
          except:
            logger.debug('Module (%s) does not contain a variable called extensions' % module.__file__)
      except EnvironmentError, e:
        logger.exception('Unable to load extension: %s' % package_name)

        raise
        
    self._loaded = True
    
  def _resolve_packages(self, package_match):
    logger.debug('Resolving packages from: %s' % package_match)
    
    parts = package_match.split('.')

    if parts[-1] == '*':
      packages          = []
      base_package_name = '.'.join(parts[0:-1])

      base_package = self._import(base_package_name)
      
      for f in os.listdir(os.path.dirname(base_package.__file__)):
        name, ext = os.path.splitext(f)
        
        if ext == '.py':
          logger.debug('Found package file: %s under base %s' % (name, base_package_name))

          packages.append('%s.%s' % (base_package_name, name))

      return packages
    else:
      return [package_match]

  def _import(self, name):
    logger.debug("Attempting to import %s" % name)

    mod = __import__(name)

    components = name.split('.')
    for comp in components[1:]:
      mod = getattr(mod, comp)

    return mod
