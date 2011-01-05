import logging
import re
from datetime import date
from fancyashow.parsers.common.google_calendar import GoogleCalendarParser

from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util
extensions = ExtensionLibrary()

logger = logging.getLogger(__name__)

class Gutter(GoogleCalendarParser):
  BACK_ROOM_RE = re.compile('^back\s+room\s*:?\s*', re.I)
  
  def _process_recurring_entries(self, entries):
    return []

  def _process_entry(self, entry):
    logger.debug("Processing entry: %s, starting on: %s" % (entry.title.text, entry.when[0].start_time))
    
    if not self.BACK_ROOM_RE.match(entry.title.text):
      return None
      
    title_txt = self.BACK_ROOM_RE.sub('', entry.title.text)

    show = Show()

    show.venue      = self.venue()
    show.performers = [Performer(p) for p in lang_util.parse_performers(title_txt)]

    show.show_time = date_util.parse_date_time(entry.when[0].start_time)

    return show
    
  def venue(self):
    return Venue('The Gutter', 'http://www.thegutterbrooklyn.com/')
    
  @classmethod
  def id(self):
    return 'us.ny.brooklyn.gutter'

  @classmethod
  def calendar_id(cls):
    return 'gutterbar@gmail.com'
    
  @classmethod
  def group_by_date(cls):
    return False

extensions.register_show_parser(Gutter)