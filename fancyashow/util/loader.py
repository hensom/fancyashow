import logging
from datetime             import datetime, timedelta, date
from fancyashow.db.models import Artist, ArtistInfo, VenueInfo, Show, ParseMeta
from fancyashow.util      import lang

logger = logging.getLogger(__name__)

class ShowLoader(object):
  def __init__(self, parser_class, resource_extractor):
    self.parser_class       = parser_class
    self.resource_extractor = resource_extractor
    
  def load_shows(self):
    parser = self.parser_class(self.resource_extractor)
    
    logger.info(u'Parsing %s' % parser.id())

    shows = []

    for show in parser:
      shows.append(show)
        
    logger.info(u'Loading %d Show[s]: %s' % (len(shows), parser.id()))
        
    old_shows = list(Show.objects.filter(parse_meta__parser_id = parser.id()))
    
    new_shows = []

    invalid_shows = []
    
    for s in shows:
      try:
        show = self._trans_show(parser, s)
        
        show.validate()

        new_shows.append(show)
      except:
        logger.exception(u'Invalid show: %s from %s' % (self._show_debug_str(s), parser.id()))
        
        invalid_shows.append(s)
    
    shows = self._reconcile_changes(old_shows, new_shows)
    
    return len(new_shows), len(invalid_shows), shows
    
  def _show_debug_str(self, s):
    if s.resources.show_url:
      return s.resources.show_url
    elif s.merge_key:
      return s.merge_key
    elif s.title:
      return s.title
    elif s.performers:
      return s.performers[0].name
    elif s.date:
      return 'on date: %s' % s.date
    else:
      return '<NO CONTEXT>'
    
  def _reconcile_changes(self, old_shows, new_shows):
    logger.debug(u'Reconciling changes between show lists %d old show[s], %d new show[s]' % (len(old_shows), len(new_shows)))

    old_by_merge_key, old_by_date = self._split_show_list(old_shows)
    new_by_merge_key, new_by_date = self._split_show_list(new_shows)
    
    shows = []
    
    shows.extend(self._merge_by_key(old_by_merge_key, new_by_merge_key))
    shows.extend(self._merge_by_date(old_by_date, new_by_date))
    
    return shows
    
  def _merge_by_key(self, old_by_merge_key, new_by_merge_key):
    shows = []
    
    logger.debug(u'Merging shows by key: old: %d, new: %d' % (len(old_by_merge_key.values()), len(new_by_merge_key.values())))

    for new_show in new_by_merge_key.values():
      old_show = old_by_merge_key.get(new_show.parse_meta.merge_key)
      
      logger.debug(u'Merging new show with key: %s, matching show found?: %s', new_show.parse_meta.merge_key, old_show is not None)
      
      if old_show:
        del old_by_merge_key[new_show.parse_meta.merge_key]

        self._merge_shows(old_show, new_show)
        
        shows.append(old_show)
      else:
        shows.extend(self._save_shows(new_show))
        
    for old_show in old_by_merge_key.values():
      old_show.delete()
      
    return shows
      
  def _merge_by_date(self, old_by_date, new_by_date):
    shows = []
    
    logger.debug(u'Merging shows by date: old: %d, new: %d' % (len(old_by_date.values()), len(new_by_date.values())))

    for date, new_shows in new_by_date.iteritems():
      old_shows = old_by_date.get(date)
      
      if not old_shows:
        shows.extend(self._save_shows(*new_shows))
      elif len(old_shows) == 1 and len(new_shows) == 1:
        shows.extend(self._merge_shows(old_shows[0], new_shows[0]))
      else:
        logger.error(u'[%s] Multiple shows found for date %s, unable to load' % (self.parser_class.id(), date))
        # Load the new shows, but set a flag to audit them
        pass
        
    return shows
          
  def _merge_shows(self, old_show, new_show):
    logger.debug(u'Merging %s with %s' % (old_show, new_show))

    copy_attrs = ('parse_meta', 'title', 'date', 'show_time', 'door_time', 'url', 'image_url', 'parsed_resources', 'venue', 'soldout')

    for attr in copy_attrs:
      setattr(old_show, attr, getattr(new_show, attr))

    artist_map = { }

    # Preserve old artist associations as they may have been manually made
    for artist in old_show.artists:
      if artist.artist_id:
        artist_map[artist.name] = artist.artist_id
        
    for artist in new_show.artists:
      artist.artist_id = artist_map.get(artist.name)
        
    old_show.artists = new_show.artists
      
    old_show.save()
    
    return [old_show]
    
  def _save_shows(self, *shows):
    for show in shows:
      show.save()
      
    return shows

  def _split_show_list(self, shows):
    by_merge_key, by_date = { },  { }
    
    for show in shows:
      if show.parse_meta.merge_key:
        by_merge_key[ show.parse_meta.merge_key ] = show
      else:
        show_date = show.date.date()
        
        if show_date not in by_date:
          by_date[show_date] = [ ]

        by_date[show_date].append(show)
        
    return by_merge_key, by_date
    
  def _show_date(self, test_date):
    if isinstance(test_date, datetime):
      if test_date.hour < 4:
        test_date = test_date - timedelta(days = 1)

      test_date = test_date.date()

    return self._force_datetime(test_date)
    
  def _force_datetime(self, date):
    if not date:
      return None
    elif isinstance(date, datetime):
      return date
    else:
      return datetime(date.year, date.month, date.day)
      
  def _trans_url(self, url):
    if url:
      return url.replace(' ', '%20')
    else:
      return None
      
  def _normalize_caps(self, text):
    if text:
      text = text.strip(' \n\r\t')

    if text and text == text.upper():
      text = ' '.join( (part.capitalize() for part in text.lower().split(' ')) )
        
    return text

  def _trans_artist(self, p):
    display_name = self._normalize_caps(p.name)

    return ArtistInfo(name = display_name, headliner = p.headliner, start_time = p.start_time,)

  def _trans_show(self, parser, s):
    def trans_venue(v):
      return VenueInfo(name = v.name, url = v.url)

    show_mappings = {
      'parse_meta':    ParseMeta(parser_id = parser.id(), merge_key = s.merge_key),
      'title':         self._normalize_caps(s.title),
      'artists':       [self._trans_artist(p) for p in s.performers],
      'soldout':       s.soldout,
      'venue':         trans_venue(s.venue),
      'date':          self._show_date(s.show_time or s.door_time or s.date),
      'show_time':     self._force_datetime(s.show_time),
      'door_time':     self._force_datetime(s.door_time),
      'url':           self._trans_url(s.resources.show_url),
      'image_url':     self._trans_url(s.resources.image_url),
      'parsed_resources': s.resources.resource_uris,
      'creation_date': datetime.now()
    }

    return Show(**show_mappings)