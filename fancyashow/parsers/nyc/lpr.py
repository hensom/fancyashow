import logging
import urlparse
import re

from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class LPR(ShowParser):
  BASE_URL         = "http://lepoissonrouge.com/"
  CALENDAR_URL     = "http://lepoissonrouge.com/calendar/%(year)s/%(month)s/"
  IS_EVENT_URL_RE  = re.compile('http://lepoissonrouge.com/events/view/\d+')
  IS_ARTIST_URL_RE = re.compile('http://lepoissonrouge.com/events/artist/\d+')
  MONTHS_AHEAD     = 3

  def __init__(self, *args, **kwargs):
    super(LPR, self).__init__(*args, **kwargs)
  
    self._current_parser = None
    self._date_queue     = self._request_dates()

  def _next_parser(self):
    if self._date_queue:
      return self._month_parser(self._date_queue.pop(0))

    return None

  def _request_dates(self):
    ret   = [ ]
    start = datetime.today().date().replace(day = 1)

    for i in xrange(self.MONTHS_AHEAD):
      month = start.month + i
      year  = start.year

      if month > 12:
        month = month - 12
        year  = year + 1

      ret.append(start.replace(month = month, year = year))

    return ret
    
  def next(self):
    if not self._current_parser:
      self._current_parser = self._next_parser()

    while(self._current_parser):
      try:
        return self._current_parser.next()
      except StopIteration:
        self._current_parser = self._next_parser()

    raise StopIteration

  def _month_parser(self, request_date):
    month_url = self.CALENDAR_URL % {'year': request_date.year, 'month': request_date.month}
  
    show_urls = html_util.get_show_urls_and_section(month_url, '#content', ".event", self.IS_EVENT_URL_RE)

    for url, show_section in show_urls.iteritems():
      yield self._parse_show(url, show_section)

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