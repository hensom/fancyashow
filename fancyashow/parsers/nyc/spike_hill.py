import logging
from datetime import date
from fancyashow.parsers.common.google_calendar import GoogleCalendarParser

from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util
extensions = ExtensionLibrary()

logger = logging.getLogger(__name__)

class SpikeHill(GoogleCalendarParser):
  def _process_recurring_entries(self, entries):
    return []

  def _process_entry_group(self, start_date, entries):
    show = Show()

    show.venue      = self.venue()
    show.performers = []
    
    entries.sort(key = lambda e: e.when[0].start_time, reverse = True)

    for entry in entries:
      logger.debug("Processing entry: %s, starting on: %s" % (entry.title.text, entry.when[0].start_time))

      # Full day events usually denote a title which we currently will simply skip
      if 'T' not in entry.when[0].start_time:
        logger.debug('Entry "%s" is an all day event, skipping' % entry.title.text)

        continue
      elif 'pub side' in entry.title.text.lower():
        logger.debug('Entry "%s" is on the Pub Side of Spike Hill, skipping' % entry.title.text)

        continue

      start_time     = date_util.parse_date_time(entry.when[0].start_time)

      show.show_time = min(start_time, show.show_time or start_time)

      show.performers.append(Performer(entry.title.text))

    return [show]
    
  def venue(self):
    return Venue('Spike Hill', 'http://www.spikehill.com/')
    
  @classmethod
  def id(self):
    return 'us.ny.brooklyn.spike-hill'

  @classmethod
  def calendar_id(cls):
    return 'sa9552dusndv1rnrgumdujsgl0@group.calendar.google.com'
    
  @classmethod
  def group_by_date(cls):
    return True
    
extensions.register_show_parser(SpikeHill)