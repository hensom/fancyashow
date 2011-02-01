from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util
import re

extensions = ExtensionLibrary()

class SantosPartyHouse(ShowParser):
  BASE_URL     = "http://www.santospartyhouse.com/"
  CALENDAR_URL = "http://www.santospartyhouse.com/"
  IS_EVENT     = re.compile("http://www.santospartyhouse.com/event/index/id/\d+")

  def __init__(self, *args, **kwargs):
    super(SantosPartyHouse, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    show_urls = html_util.get_show_urls(self.CALENDAR_URL, "#calendar-container", 'td', self.IS_EVENT)
    
    for url in show_urls:
      yield self._parse_show(url)

  def _parse_show(self, link):
    event_doc    = html_util.fetch_and_parse(link)
    
    event_detail = event_doc.get_element_by_id('eventDetail')
    
    title_txt    = []

    found_h_el   = False
    
    # Start parsing when we find the first h* element
    # Stop parsing if we found an h* element, but then encounter anything else
    for el in event_detail.getchildren():
      if el.tag in ('h1', 'h2'):
        found_h_el = True

        if el.text_content():
          title_txt.append(el.text_content())
      elif found_h_el:
        break

    """
    <span id="timeDetail">
      Apr 24, 2010<br />
			upstairs<br />
    	Doors @ 7 PM<br/>
    	$15.00 Adv. / $20 at the Door<br />
    	<a href="http://www.deadcellentertainment.tix.com/Schedule.asp?OrganizationNumber=2690" target="_blank">
        <img src="/images/buyticket.png" alt="Purchase Tickets" />
      </a>
    </span>
    """
    time_el  = event_detail.get_element_by_id("timeDetail")
    date_txt = time_el.text
    time_txt = time_el.text_content()
    
    performers = [] 

    show = Show()

    show.merge_key  = link
    show.venue      = self.venue()
    show.performers = [Performer(p) for p in lang_util.parse_performers('/'.join(title_txt))]
    show.door_time  = date_util.parse_show_time(date_txt, time_txt)
    show.show_time  = date_util.parse_door_time(date_txt, time_txt)
    
    show.resources.show_url      = link
    show.resources.resource_uris = self.resource_extractor.extract_resources(event_detail)
    
    img = html_util.get_first_element(event_detail, "img")
    
    if img is not None:
      show.resources.image_url  = img.get('src')

    return show

  def venue(self):
    return Venue('Santos Party House', self.BASE_URL)

  @classmethod
  def id(cls):
    return 'us.ny.manhattan.santos-party-house'

extensions.register_show_parser(SantosPartyHouse)
