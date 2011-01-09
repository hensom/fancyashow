from __future__ import absolute_import

import cgi
import logging
import lxml.html
from facebook                     import GraphAPI
from datetime                     import datetime
from fancyashow.extensions        import ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

LOG = logging.getLogger(__name__)

class FacebookParser(ShowParser):
  EVENT_URL = 'http://www.facebook.com/event.php?eid=%s'
  
  def __init__(self, *args, **kwargs):
    super(FacebookParser, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration
    
  def _get_parser(self):
    api    = GraphAPI(self.settings['facebook_access_token'])
    events = api.get_connections(self.profile_id(), 'events')
    
    today     = datetime.today() 
    event_ids = []
    
    for event_info in events['data']:
      start_time = date_util.parse_date_time(event_info['start_time'])
      
      if start_time >= today:
        event_ids.append(event_info['id'])
        
    if event_ids:
      parse_events = api.get_objects(event_ids)

      for event in parse_events.values():
        yield self._parse_show(api, event)

  def _parse_show(self, api, event):
    LOG.debug('Parsing event: %s' % event['id'])

    show = Show()

    show.merge_key  = event['id']
    show.venue      = self.venue()
    show.performers = [Performer(p) for p in lang_util.parse_performers(event['name'])]
    show.show_time  = date_util.parse_date_time(event['start_time'])
    
    html_doc = u'<html><body>%s</body></html>' % cgi.escape(event.get('description', ''))
    doc      = lxml.html.document_fromstring(html_doc)

    show.resources.show_url      = self.EVENT_URL % event['id']
    show.resources.resource_uris = self.resource_extractor.extract_resources(doc)

    return show

  @classmethod
  def profile_id(cls):
    raise NotImplementedError()
    
  @classmethod
  def venue(cls):
    raise NotImplementedError()