import logging
import re
from datetime                     import datetime
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

logger = logging.getLogger(__name__)

extensions = ExtensionLibrary()

class CakeShop(ShowParser):
  BASE_URL     = "http://cake-shop.com/"
  DATE_RE      = re.compile("\w+\s+(?P<day>\d+)")
  NUM_RE       = re.compile('^\s*\d+\s*(?:st|nd|rd|th):\s*$', re.IGNORECASE | re.MULTILINE)
  TIME_RE      = re.compile('^\s*(?P<time>\d+(?::\d+)?\s*(?:am|pm))\s*', re.IGNORECASE | re.MULTILINE)
  PRICE_OR_AGE = re.compile('(?:\$\d+|\d+\+)', re.IGNORECASE | re.MULTILINE)
  MONTHS_AHEAD = 1
  
  def __init__(self, *args, **kwargs):
    super(CakeShop, self).__init__(*args, **kwargs)
    
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

      if month > 12:
        month = month - 12

      ret.append(start.replace(month = month))
      
    return ret

  def _month_parser(self, request_date):
    month_url = '%scalendar/%s.html' % (self.BASE_URL, request_date.strftime('%b%y').lower())
    
    logger.debug('Parsing: %s' % month_url)

    doc = html_util.fetch_and_parse(month_url)
    
    main_table = html_util.get_first_element(doc, 'body > table')
    
    trs = main_table.getchildren()
    
    # Remove the "header" row from the table
    trs.pop(0)
    # Remove the "footer" row from the table
    trs.pop()
    
    # The remaining rows look as follows:
    # The Show Details/Time pairing might be repeated
    """
    <tr><td>Monday 4th</td></tr>
    <tr><td>
      <center>
        <p>Show Details</p>
        <p>Show Time</p>
      </center>
    </td></tr>
    """
    
    while trs:
      date_row, show_row = trs.pop(0).getchildren(), trs.pop(0).getchildren()
      
      for i, date_td in enumerate(date_row):
        # At the end of the month, the html doesn't always contain a corresponding table
        # cell in the show_row for each date in the date_row
        if i > len(show_row) - 1:
          break

        date_match = self.DATE_RE.match(date_td.text_content().strip())
        
        if date_match:
          show_date = request_date.replace(day = int(date_match.group('day')))

          show_td = show_row[i]
          
          p_list = show_td.cssselect('center > p')
      
          if len(p_list) % 2 == 0:
            while p_list:
              show_detail, show_time = p_list.pop(0), p_list.pop(0)

              try:
                show = self._parse_show(show_date, show_detail, show_time)
                
                if not (show.door_time or show.show_time):
                  logger.warning('Unable to determine door or show time for show on %s, discarding' % show_date)
                elif not (show.title or len(show.performers) > 0):
                  logger.warning('Unable to determine title or performers for show on %s, discarding' % show_date)
                else:
                  yield show                  
              except Exception, e:
                raise ParserError(None, show_detail, e)
          
  def _parse_show(self, show_date, show_detail, show_time):
    show = Show()
    
    time_txt = ','.join([p for p in show_time.text_content().split(',') if not self.PRICE_OR_AGE.search(p)])

    logger.debug('Show: %s - %s' % (time_txt, show_time.text_content().strip(' \n')))
    show.venue      = self.venue()
    show.performers = self._parse_performers(show_detail)
    show.show_time  = date_util.parse_show_time(show_date, time_txt)
    show.door_time  = date_util.parse_door_time(show_date, time_txt)

    # TODO right now the below parsing doesn't work, so just skip these shows for now
    if not show.show_time and not show.door_time:
      time_match = self.TIME_RE.search(time_txt)
      
      if time_match:
        show.door_time = date_util.parse_date_and_time(show_date, time_match.group('time'))

    show.resources.resource_uris = self.resource_extractor.extract_resources(show_detail, show_time)

    # TODO work could be done here to find larger images (sometimes the img's are enclosed in an anchor tag)
    for img_tag in show_detail.iter(tag = 'img'):
      src = img_tag.get('src')
      
      # Skip the images that show the early shows, later shows, and the 5 years logo
      if not ('early' in src or 'later' in src or '5years' in src):
        show.resources.image_url = src
        
        break

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
      performer_is_next = self.NUM_RE.search(start_time_txt) or self.TIME_RE.search(start_time_txt)
    else:
      performer_is_next = False
    
    for e in show_detail.getchildren():
      text = e.tail or e.text_content()

      if performer_is_next and text:
        performer_is_next = False

        headliner = e.tag == 'span' and html_util.has_class(e, 'headliner')

        time_match = self.TIME_RE.search(start_time_txt)

        if time_match and not self.NUM_RE.search(start_time_txt):
          start_time = time_match.group('time')
        else:
          start_time = None
          
        performers.append(Performer(text, start_time = start_time, headliner = headliner))
      elif text:
        start_time_txt    = text
        performer_is_next = self.NUM_RE.search(start_time_txt) or date_util.TIME_RE.search(start_time_txt)

    return performers
    
  def venue(self):
    return Venue('Cake Shop', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.cake-shop'

extensions.register_show_parser(CakeShop)