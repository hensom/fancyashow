import logging
import urlparse
import re

from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class LPR(ShowParser):
  BASE_URL         = "http://lepoissonrouge.com/"
  CALENDAR_URL     = "http://lepoissonrouge.com/calendar"
  IS_EVENT_URL_RE  = re.compile('http://lepoissonrouge.com/events/view/\d+')
  IS_ARTIST_URL_RE = re.compile('http://lepoissonrouge.com/events/artist/\d+')

  def __init__(self, *args, **kwargs):
    super(LPR, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration
    
  def _get_parser(self):
    show_urls = html_util.get_show_urls_and_section(self.CALENDAR_URL, '#content', ".event", self.IS_EVENT_URL_RE)

    for url, show_section in show_urls.iteritems():
      try:
        yield self._parse_show(url, show_section)
      except Exception, e:
        raise ParserError(url, show_section, e)

  def _parse_show(self, link, show_section):
    show_doc    = html_util.fetch_and_parse(link)

    show_detail = show_doc.get_element_by_id("content")
    
    title       = html_util.get_first_element(show_detail, '.title').text

    date_txt    = html_util.get_first_element(show_section, '.date').text
    image_url   = html_util.get_first_element(show_detail,  '.left-view-header img').get('src')
    
    performers = []
    
    performer_detail = html_util.get_first_element(show_detail, '.performers')
    performer_urls   = []
    
    for anchor in performer_detail.iter(tag = 'a'):
      performers.extend(self._parse_performers(anchor))
      
      if self.IS_ARTIST_URL_RE.match(anchor.get('href')):
        performer_urls.append(anchor.get('href'))
        
    resource_sections = [show_section, show_detail]
    
    for url in performer_urls:
      resource_sections.extend(self.fetch_performer_content(url))
    
    show = Show()

    show.merge_key               = link
    show.venue                   = self.venue()
    show.performers              = performers
    show.show_time               = date_util.parse_date_time(date_txt)
    show.resources.show_url      = link
    show.resources.image_url     = image_url
    show.resources.resource_uris = self.resource_extractor.extract_resources(*resource_sections)

    return show

  def _parse_performers(self, a):
    name = a.text_content()

    if html_util.has_class(a, 'headliner'):
      return [Performer(name, headliner = True)]
    elif html_util.has_class(a, 'opener'):
      return [Performer(name, headliner = False)]

    return []
    
  def fetch_performer_content(self, url):
    doc = html_util.fetch_and_parse(url)
    
    return doc.cssselect('#content')
    
  def show_list_url(self):
    return self.venue().url + 'events'
    
  def event_url_re(self):
    return re.compile(self.venue().url + 'event/\d+')

  def venue(self):
    return Venue('Le Poisson Rouge', 'http://www.lepoissonrouge.com/')

  @classmethod
  def id(cls):
    return 'us.ny.manhattan.lpr'

extensions.register_show_parser(LPR)