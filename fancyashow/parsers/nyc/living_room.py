import logging
import re

from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

logger = logging.getLogger(__name__)

TIME_MATCH = '\d+(?::\d+)?\s*(?:am|pm)'

class LivingRoom(ShowParser):
  BASE_URL     = "http://www.livingroomny.com/"
  DATE_RE      = re.compile("\w+\s+(?P<day>\d+)")
  TIME_RE      = re.compile('\s*(?P<time>%s)\s*(?:\s*-\s*)?(?:(?P<time_to>%s)\s*-\s*)?' % (TIME_MATCH, TIME_MATCH), re.IGNORECASE | re.MULTILINE)
  MONTHS_AHEAD = 3
  
  def __init__(self, *args, **kwargs):
    super(LivingRoom, self).__init__(*args, **kwargs)
    
    self._current_parser = None
    self._date_queue     = self._request_dates()
    
  def _next_parser(self):
    if self._date_queue:
      return self._month_parser(self._date_queue.pop(0))
      
    return None
  
  def next(self):
    if not self._current_parser:
      self._current_parser = self._next_parser()
      
    while(self._current_parser):
      try:
        return self._current_parser.next()
      except StopIteration:
        self._current_parser = self._next_parser()
    
    raise StopIteration

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

  def _month_parser(self, request_date):
    month_url = '%scalendar/%d-%d' % (self.BASE_URL, request_date.year, request_date.month)
    
    logger.debug('Parsing: %s' % month_url)

    doc = html_util.fetch_and_parse(month_url)
    
    main_table = html_util.get_first_element(doc, '.month-view table')
    
    for td in html_util.get_elements(main_table, 'td.has-events'):
      for show in self._parse_shows(request_date, td):
        yield show
          
  def _parse_shows(self, base_date, td):
    day = int(html_util.get_first_element(td, '.day').text_content())
    
    date = base_date.replace(day = day)
    
    logger.debug('Parsing shows on %s' % date.strftime('%F'))
    
    lr_shows     = html_util.get_elements(td, '.lr_color a')
    googie_shows = html_util.get_elements(td, '.googie_color a')
    
    shows = []
    
    if lr_shows:
      shows.append(self._parse_show(date, lr_shows))
      
    if googie_shows:
      shows.append(self._parse_show(date, googie_shows))
      
    return shows
      
  def _parse_artist(self, a):
    time_match = self.TIME_RE.match(a.text_content())
    
    if time_match:
      start_time = time_match.group('time')
      name       = self.TIME_RE.sub('', a.text_content())
    else:
      start_time = None
      name       = a.text_content()

    link = a.get('href')
    
    if link:
      artist_doc = html_util.fetch_and_parse(link)
      
      artist_el  = html_util.get_first_element(artist_doc, '#bleh')
    else:
      artist_el = None

    logging.debug('Artist (%s) name: %s from (%s)' % (start_time, name, a.text_content()))
      
    return (name, start_time, artist_el)
      
  def _parse_show(self, base_date, links):
    performers = []
    
    show_time  = None
    
    resource_els = []

    for a in links:
      # Every other link on the calendar seems to have no text
      if a.text_content():
        name, start_time_txt, artist_el = self._parse_artist(a)
      
        if artist_el is not None:
          resource_els.append(artist_el)
      
        if start_time_txt:
          start_time = date_util.parse_date_and_time(base_date, start_time_txt)
        
          if not show_time or start_time < show_time:
            show_time = start_time

        performers.append(Performer(name, start_time = start_time_txt))
      
    # Performers are list from first to last
    performers.reverse()
    resource_els.reverse()

    show = Show()

    show.venue      = self.venue()
    show.performers = performers
    show.date       = base_date
    show.show_time  = show_time

    show.resources.resource_uris = self.resource_extractor.extract_resources(*resource_els)

    image_url = None

    for el in resource_els:
      if image_url:
        break

      for img_tag in el.iter(tag = 'img'):
        image_url = img_tag.get('src')
        
        break

    show.resources.image_url = image_url

    return show
    
  def _parse_performers(self, show_detail):
    performers = []

    """
    Without times:
    <img src="images/5years.jpg">
    <br><Br> 
    5TH:<BR>
    <span class="headliner"><a href="http://www.myspace.com/thestyrenes" target="_blank">STYRENES</span></a><br>
    <span class="city"> [35TH ANNIVERSARY TOUR!!!] </span><br> 
    <a href="http://www.myspace.com/styrenes" target="_blank"> 
    <img src="images/styrenes.jpg"> 
    </a><br><br>
    
    """
    
    """
    With times:

    8PM:<BR>
    <span class="headliner"><a href="http://www.myspace.com/tyvekmusic" target="_blank">TYVEK</span></a><br>
    <span class="city">[detroit]</span><br>
    <a href="http://www.myspace.com/tyvekmusic" target="_blank"> 
    <img src="images/tyvek.jpg"> 
    </a><br><br> 
    """
    
    start_time_txt    = show_detail.text
    
    if start_time_txt:
      performer_is_next = self.NUM_RE.search(start_time_txt) or date_util.TIME_RE.search(start_time_txt)
    else:
      performer_is_next = False
    
    for e in show_detail.getchildren():
      text = e.tail or e.text_content()

      if performer_is_next and text:
        performer_is_next = False

        headliner = e.tag == 'span' and html_util.has_class(e, 'headliner')

        time_match = date_util.TIME_RE.search(start_time_txt)

        if time_match and not self.NUM_RE.search(start_time_txt):
          logger.debug('Got start time: %s' % start_time_txt)
          start_time = time_match.group('time')
        else:
          start_time = None

        performers.append(Performer(text, start_time = start_time, headliner = headliner))
      elif text:
        start_time_txt    = text
        performer_is_next = self.NUM_RE.search(start_time_txt) or date_util.TIME_RE.search(start_time_txt)

    return performers
    
  def venue(self):
    return Venue('Living Room', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.manhattan.living-room'

extensions.register_show_parser(LivingRoom)