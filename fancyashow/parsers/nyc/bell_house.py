import re
from datetime                     import datetime, timedelta
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class BellHouse(ShowParser):
  BASE_URL     = "http://www.thebellhouseny.com/"
  CALENDAR_URL = "http://www.thebellhouseny.com/calendar.php"
  DATE_RE      = re.compile("\w+ (?P<month>\d+)/(?P<day>\d+):")
  TIME_RE      = re.compile(':\s+(?P<time>\d+(?:\s*:\s*\d+)?\s*[ap]m)\s*', re.IGNORECASE)
  
  def __init__(self, *args, **kwargs):
    super(BellHouse, self).__init__(*args, **kwargs)
    
    self._parser = None
  
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    today = datetime.today().date()

    doc   = html_util.fetch_and_parse(self.CALENDAR_URL)

    main_section = doc.get_element_by_id("col-main")

    for event_detail in main_section.cssselect("#bellhouse"):
      try:
        yield self._parse_show(self.CALENDAR_URL, event_detail, today)
      except Exception, e:
        raise ParserError(self.CALENDAR_URL, event_detail, e)

  def _parse_show(self, show_url, event_detail, today):
    show = Show()

    # Bell House will have duplicate instances of #unionhall_performer
    # some may or may not have links, but those that do have links are tagged
    # with the same id again ie: <div id="bellhouse_performer"><a href="#" id="#bellhouse_performer"> ...
    performers = [Performer(p.text_content()) for p in event_detail.cssselect("#bellhouse_performer") if p.tag != 'a']
    
    performers[0].headliner = True

    ticket_link = html_util.get_first_element(event_detail, '#ticket_link a', optional = True)

    show.venue      = self.venue()
    show.performers = performers
    
    if ticket_link is not None:
      show.merge_key = ticket_link.get('href')

    # Format: THU 3/25: 6pm / $15      
    date_tag   = event_detail.get_element_by_id("bellhouse_date")

    date_match = self.DATE_RE.match(date_tag.text_content())
    time_match = self.TIME_RE.search(date_tag.text_content())

    if date_match and time_match:
      month, day = (int(d) for d in (date_match.group('month'), date_match.group('day')))
      
      date_txt = today.replace(month = month, day = day).strftime('%F')
      
      show.show_time = date_util.parse_date_and_time(date_txt, time_match.group('time'))

    show.resources.resource_uris = self.resource_extractor.extract_resources(event_detail)

    for img_tag in event_detail.iter(tag = 'img'):
      show.resources.image_url = img_tag.get('src')
      
      break
      
    return show

  def venue(self):
    return Venue('The Bell House', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.bell-house'

extensions.register_show_parser(BellHouse)