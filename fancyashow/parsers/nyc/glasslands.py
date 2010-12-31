import feedparser
import logging
import lxml.html
import re
from   lxml.html.clean import Cleaner
from fancyashow.extensions        import ExtensionLibrary, ShowParser
from fancyashow.extensions.models import Venue, Performer, Show
from fancyashow.util              import parsing  as html_util
from fancyashow.util              import dates    as date_util
from fancyashow.util              import lang     as lang_util

extensions = ExtensionLibrary()

class Glasslands(ShowParser):
  BASE_URL        = "http://www.glasslands.com/"
  FEED_URL        = "http://glasslands.blogspot.com/feeds/posts/default"
  SHOW_DIVIDER_RE = re.compile('___+')
  HEADER_SEP_RE   = re.compile('(?:(?:&gt;)|/){2}')
  BODY_SKIP       = [
    re.compile('rsvp',    re.I),
    re.compile('tickets', re.I)
  ]
  REPLACEMENTS    = [
    (re.compile('<\s*br\s*/?\s*>', re.I), '\n'),
    (re.compile('<\s*div\s*.*?>',  re.I), ''),
    (re.compile('<\s*/\s*div\s*>', re.I), '\n'),
    (re.compile('details\s+tba', re.I),   '')
  ]

  def __init__(self, *args, **kwargs):
    super(Glasslands, self).__init__(*args, **kwargs)
    
    self._parser = None    
    
  def next(self):
    if not self._parser:
      self._parser = self._get_parser()

    while(True):
      return self._parser.next()

    raise StopIteration

  def _get_parser(self):
    f = feedparser.parse(self.FEED_URL)
    
    for entry in f.entries:
      for show in self._parse_shows(entry):
        yield show

  def _parse_shows(self, entry):
    content = None
    shows   = []
    
    entry_date = date_util.parse_date_time(entry.published)

    for item in entry.content:
      if item.type in ('text/html',):
        content = item.value

    if not content:
      logging.error('Unable to extract content from entry: %s' % entry.id)

      return []
      
    # This next part is technically pretty evil
    entry_doc = lxml.html.fromstring(content)

    tags = ['span', 'b', 'i', 'strong', 'em']

    cleaner = Cleaner(remove_tags = tags, links = False)

    clean_content = cleaner.clean_html(entry_doc)
  
    # FIXME patch lxml to handle this while calling text_content()
    # http://codespeak.net/pipermail/lxml-dev/2008-August/004009.html  
    content_str = lxml.html.tostring(clean_content)
    
    for regexp, replacement in self.REPLACEMENTS:
      content_str = regexp.sub(replacement, content_str)
  
    for part in self.SHOW_DIVIDER_RE.split(content_str):
      part = part.strip(' \t\n')
      
      parts = part.split('\n')
      
      header = parts.pop(0)
      body   = '\n'.join(parts)
      
      header_parts = self.HEADER_SEP_RE.split(header)

      date_txt = header_parts.pop(0)
      time_txt = None
      
      for part in header_parts:
        if date_util.STRICT_TIME_RE.search(part):
          time_txt = date_util.sanitize_time(part)
          
          break
          
      if not time_txt:
        logging.error('Unable to find time in header: %s' % header)
        
        continue

      if '-' in time_txt:
        time_txt = time_txt.split('-')[0].strip()
        
      if not(time_txt.endswith('am') or time_txt.endswith('pm')):
        time_txt = time_txt + 'pm'

      show_doc = lxml.html.fromstring(body)
      
      use_all         = False
      performer_parts = []
      all_parts       = []
      
      for el in show_doc.iter():
        if self._is_img(el):
          break

        text = el.text or ''
        tail = el.tail or ''
  
        for regexp in self.BODY_SKIP:
          if regexp.search(text):
            text = ''

          if regexp.search(tail):
            tail = ''
        
        for p in (text, tail):
          if p:
            all_parts.append(p)

        if text and el.tag != 'a':
          use_all = True
        
        if el.tag == 'a' and tail.strip() not in(',', '&', 'w/', ''):
          use_all = True

        if el.tag == 'a':
          performer_parts.append(text)

      img_url = None
      
      for img in show_doc.iter(tag = 'img'):
        if img.get('src'):
          img_url = img.get('src')
          
          break
          
      show = Show()
      
      show.venue = self.venue()
      
      if use_all:
        performers_str  = ' '.join(all_parts).replace(' ,', ',').replace('  ', ' ')

        show.performers = [Performer(name) for name in lang_util.parse_performers(performers_str)]
      else:
        show.performers = [Performer(name) for name in performer_parts if name]
      
      try:
        show.show_time = date_util.parse_date_and_time(date_txt, time_txt)
      except:
        logging.exception('Unable to parse: %s - %s' % (date_txt, time_txt))
        continue

      show.resources.image_url     = img_url
      show.resources.resource_uris = self.resource_extractor.extract_resources(show_doc)

      date_util.adjust_fuzzy_years(show, entry_date)

      shows.append(show)

    return shows
    
  def _is_img(self, el):
    if el.tag == 'img':  
      return True
    elif el.tag == 'a':      
      for img in el.iter(tag = 'img'):
        return True
        
      return False

  def venue(self):
    return Venue('Glasslands', self.BASE_URL)
    
  @classmethod
  def id(cls):
    return 'us.ny.brooklyn.glasslands'
    
extensions.register_show_parser(Glasslands)