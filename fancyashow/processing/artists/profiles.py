import logging
from datetime              import datetime
from fancyashow.extensions import ArtistProcessor, ResourceExtractorManager
from fancyashow.extensions import ExtensionLibrary

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

# State form
# $system_id:$profile_id -> {
#  last_parsed: $timestamp,
#  resources:   []
#}

class ProfileParser(ArtistProcessor):
  def __init__(self, library, settings):
    super(ProfileParser, self).__init__(library, settings)

    self.update_interval    = self.get_required_setting(settings, 'update_interval')
    self.resource_extractor = ResourceExtractorManager(library.resource_extractors())

  @classmethod
  def default_state(self):
    return { }

  def process(self, artist, state, dependent_states):
    new_state = self.clone_state(state)
    media     = []
    
    parsers = [p(self.resource_extractor) for p in self.library.artist_profile_parsers()]
    
    for profile in artist.profiles:
      for parser in parsers:
        if parser.supports(profile) and self.should_parse(artist, profile, parser, state):
          try:
            last_updated = datetime.now()

            result = parser.parse(artist, profile)
            
            key = self.parser_state_key(artist, profile, parser)
            
            if key not in new_state:
              new_state[key] = { }
              
            new_state[key].update({
              'last_updated': last_updated,
              'resources':    result.resources
            })
          except:
            logging.exception('[artist:%s] Profile parser %s failed to parse profile %s/%s' % (artist.id, parser.id(), profile.system_id, profile.profile_id))
      
    return new_state
    
  def parser_state_key(self, artist, profile, parser):
    return '%s/%s:%s' % (parser.id(), profile.system_id, profile.profile_id)

  def should_parse(self, artist, profile, parser, state):
    key = self.parser_state_key(artist, profile, parser)

    if key in state:
      last_run = state[key]['last_updated']
      now      = datetime.now()

      logger.debug('[artist:%s] Profile parser: %s for profile: %s/%s was last run on %s, update interval is %s' % (artist.id, parser.id(), profile.system_id, profile.profile_id, last_run, self.update_interval))
      
      return last_run + self.update_interval < now
    else:
      logger.debug('[artist:%s] Profile parser: %s has never been run on profile: %s/%s' % (artist.id, parser.id(), profile.system_id, profile.profile_id))

      return True

  def merge_media(self, show, media):
    for m in media:
      if isinstance(m, AudioInfo):
        show.add_or_update_audio(m.get_audio())
      elif isinstance(m, VideoInfo):
        show.add_or_update_video(m.get_video())
      else:
        raise Exception('Unsupported media type: %s' % m.__class__)

  def cleanup(self, show, state):
    pass
      
  @classmethod    
  def id(self):
    return 'profile-parser'
    
  @classmethod
  def depends_on(self):
    return ()

extensions.register_artist_processor(ProfileParser)