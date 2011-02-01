import re
from datetime                     import datetime, timedelta
from fancyashow.extensions        import ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

class MyspaceParser(ShowParser):
  BASE_URL      = "http://www.myspace.com/%s/shows"
  IS_EVENT      = re.compile("http://www.myspace.com/events/View/\d+/[^#]+$", re.I)
  
  def __init__(self, *args, **kwargs):
    super(MyspaceParser, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration
    
  def _get_parser(self):
    events_url = self.BASE_URL % self.profile_id()

    shows      = html_util.get_show_urls_and_section(events_url, ".content ul.eventsList", ".event", self.IS_EVENT)
    
    for url, section in shows.iteritems():
      yield self._parse_show(url, section)

  def _parse_show(self, url, section):
    doc = html_util.fetch_and_parse(url)

    show_el  = html_util.get_first_element(doc, '#detailPage')
    date_txt = html_util.get_first_element(show_el, 'time.dtstart').get('datetime')

    title = html_util.get_first_element(section, 'h4').text_content()

    show = Show()

    show.merge_key  = url
    show.venue      = self.venue()
    show.performers = [Performer(p) for p in lang_util.parse_performers(title)]
    show.show_time  = date_util.parse_date_time(date_txt)

    show.resources.show_url      = url
    show.resources.resource_uris = self.resource_extractor.extract_resources(section, show_el)

    return show

  @classmethod
  def profile_id(cls):
    raise NotImplementedError()
