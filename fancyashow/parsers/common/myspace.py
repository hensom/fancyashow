import re
from datetime                     import datetime, timedelta
from fancyashow.extensions        import ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

class MyspaceParser(ShowParser):
  BASE_URL      = "http://events.myspace.com/%(profile_id)s/Events/%(page)s"
  TITLE_CLEANER = re.compile("^.*? at (.*?),\s*[^,]+,\s*[^,]+$", re.M)
  IS_EVENT      = re.compile("http://events.myspace.com/Event/\d+")
  
  def __init__(self, *args, **kwargs):
    super(MyspaceParser, self).__init__(*args, **kwargs)
    
    self._parser = None
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration
    
  def num_pages(self):
    pages     = 0
    
    doc       = html_util.fetch_and_parse(self.page_url(1))
    paginator = html_util.get_first_element(doc, '#myPanel-paginate .paginateCenter', optional = True)
    
    if paginator == None:
      return 1
    
    for a in paginator.iter(tag = 'a'):
      pages = int(a.get('title'))
      
    if pages == 0:
      raise Exception("Unable to determine the number of pages")
    
    return pages
    
  def page_url(self, page_num):
    return self.BASE_URL % {'profile_id': self.profile_id(), 'page': page_num}

  def _get_parser(self):
    num_pages = self.num_pages()
    
    for i in range(1, num_pages + 1):
      events_url = self.page_url(i)

      shows      = html_util.get_show_urls_and_section(events_url, "#home-rec-events", ".eventitem", self.IS_EVENT)
    
      for url, section in shows.iteritems():
        yield self._parse_show(url, section)

  def _parse_show(self, url, section):
    today    = datetime.now()
    tomorrow = today + timedelta(days = 1)
    
    date_map = {
      'Today':    today,
      'Tomorrow': tomorrow
    }

    title    = html_util.get_first_element(section, '.event-titleinfo').text_content()
    date_txt = html_util.get_first_element(section, '.event-cal').text_content().replace('@', 'at').strip()
    
    for search, replace in date_map.iteritems():
      if date_txt.startswith(search):
        date_txt = date_txt.replace(search, replace.strftime('%F'))

        break

    print "Parsing title: %s" % title

    title    = self.TITLE_CLEANER.sub('\\1', title)
    
    print "Parsed title: %s" % title

    show = Show()

    show.merge_key  = url
    show.venue      = self.venue()
    show.performers = [Performer(p) for p in lang_util.parse_performers(title)]
    show.show_time  = date_util.parse_date_time(date_txt)

    show.resources.show_url      = url
    show.resources.resource_uris = self.resource_extractor.extract_resources(section)

    return show

  @classmethod
  def profile_id(cls):
    raise NotImplementedError()