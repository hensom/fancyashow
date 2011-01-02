from StringIO import StringIO
import logging
import lxml.html
import lxml.etree
import urllib2
import re

logger = logging.getLogger(__name__)

REPLACEMENTS = [
  (re.compile('<\s*br\s*/?\s*>', re.I), '\n'),
  (re.compile('<\s*div\s*.*?>',  re.I), ''),
  (re.compile('<\s*/\s*div\s*>', re.I), '\n')
]

def fetch_and_parse(url, parse_500 = False):
  logger.debug('Fetching: %s' % url)

  try:
    data = urllib2.urlopen(url).read()
  except urllib2.HTTPError, e:
    if parse_500 and e.getcode() == 500:
      data = e.read()
    else:
      raise

  doc = lxml.html.document_fromstring(data)

  doc.make_links_absolute(url)

  return doc
  
def has_class(el, class_name):
  for css_class in el.get('class', '').split(' '):
    if css_class and css_class == class_name:
      return True
  
  return False
  
def get_elements(el, pattern):
  if callable(pattern):
    return pattern(el)
  elif isinstance(pattern, dict):
    return el.iterchildren(**pattern)
  elif not pattern:
    return el
  else:
    return el.cssselect(pattern)
  
def get_first_element(el, pattern, optional = False):
  elements = get_elements(el, pattern)
  
  for e in elements:
    return e
    
  if optional:
    return None
  else:
    raise Exception('Unable to find element matching pattern: %s' % pattern)

def get_show_urls_and_section(url, show_list_section, show_elements, show_url_re, parse_500 = False):
  logging.debug('Fetching shows from: %s (section: "%s", elements: "%s")' % (url, show_list_section, show_elements))

  doc = fetch_and_parse(url, parse_500)

  main_section = get_first_element(doc, show_list_section)

  show_urls = { }

  for show_detail in get_elements(main_section, show_elements):
    for link in show_detail.iter('a'):
      url = link.get('href')
      
      logging.debug('Testing if "%s" is a show url' % url)

      if url and show_url_re.match(url):
        show_urls[url] = show_detail
        
  return show_urls
        
def get_show_urls(url, show_list_section, show_elements, show_url_re, parse_500 = False):
  show_map = get_show_urls_and_section(url, show_list_section, show_elements, show_url_re, parse_500)   

  return show_map.keys()
  
def get_displayed_text_content(el):
  content_str = lxml.html.tostring(el)
  
  for regexp, replacement in REPLACEMENTS:
    content_str = regexp.sub(replacement, content_str)
    
  return lxml.html.fromstring(content_str).text_content()
  
LINE_BREAK_ELS = (
  'div', 'br', 'li', 'dt', 'dd', 'table', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
)

PRESERVE_ELS = (
  'pre'
)

SKIP_ELS = (
  'script', 'embed', 'style', 'head', 'title'
)

SPACES_RE = re.compile('\s+')

def get_displayed_text_content(el):
  text = StringIO()
  
  def clean(text):
    text = SPACES_RE.sub(' ', text.replace('\n', ' ').strip())

    if not text.endswith('\n') and text != '':
      text += ' '
      
    return text

  def parse_text(el, text, preserve_text = False):
    if el.tag in SKIP_ELS:
      return
      
    if el.tag in LINE_BREAK_ELS and text.getvalue()[-1] != '\n':
      text.write('\n')

    if el.text:
      if preserve_text:
        text.write(el.text)
      else:
        text.write(clean(el.text))
    
    for child in el.getchildren():
      if child.tag is lxml.etree.Comment:
        continue
  
      parse_text(child, text, preserve_text or (child.tag in PRESERVE_ELS))
      
    if el.tag in LINE_BREAK_ELS:
      text.write('\n')
      
    if el.tail:
      # Special attendtion must be taken here since we don't want to
      # honor preserve_text if we're closing an element whose content
      # was to be preserved
      if el.tag in PRESERVE_ELS:
        preserve_tail = False
      else:
        preserve_tail = preserve_text

      if preserve_tail:
        text.write(el.tail)
      else:
        text.write(clean(el.tail))
      
  parse_text(el, text, el.tag in PRESERVE_ELS)
    
  return text.getvalue()
  
def get_name_from_title(url, name_re):  
  logger.debug('Fetching document name of: %s' % url)
  
  html = urllib2.urlopen(url).read()
  
  doc  = lxml.html.document_fromstring(html)
  
  for title in doc.iter(tag = 'title'):
    logger.debug('Fetching profile name from: %s' % title.text_content())

    match = name_re.match(title.text_content())
    
    if match:
      name = match.group(1).strip()

      logger.debug("Name from document is: %s" % name)

      return name
      
  raise Exception('Unable to determine document name: %s' % url)