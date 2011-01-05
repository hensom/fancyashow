import difflib
import re
from django.utils.stopwords import strip_stopwords

PRESENTS       = re.compile('^.*?present[s]?:?\s*', re.I)
AND            = re.compile('^\s*(?:and)|&\s*', re.I)
PERFORMERS_SEP = re.compile(',|(?:w/)|(?:with)|/', re.I)

NOT_WORD_NUM_RE = re.compile('[^\d\w\s]')

def normalize(text):
  if not text:
    text = ''

  text = strip_stopwords(text)

  return NOT_WORD_NUM_RE.sub('', text)

def artist_matches(artist_name, test):
  if not artist_name or not test:
    return False

  artist_name = normalize(artist_name).lower()
  test        = normalize(test).lower()

  match =  difflib.SequenceMatcher(None, artist_name, test).ratio() > 0.85
  
  if match:
    return True
  elif artist_name in test:
    return True
  else:
    return False
    
def artist_mentioned(artist_name, test):
  if not artist_name or not test:
    return False

  artist_name = normalize(artist_name).lower()
  test        = normalize(test).lower()
  
  return artist_name in test

def parse_performers(inp):
  inp   = PRESENTS.sub('', inp)

  parts = []

  for p in PERFORMERS_SEP.split(inp):    
    # Some venues use () instead of a comma, ie:
    # Beach Fossils (DJ Set) Apache Beat
    sub_parts = p.split(')')
    num_parts = len(sub_parts)

    for i, sub_p in enumerate(sub_parts):
      # Only add the ) back if we did a split and are not processing the last item
      if num_parts > 1 and i + 1 != num_parts:
        sub_p = sub_p + ')'

      sub_p = sub_p.strip()

      if sub_p != '':
        parts.append(sub_p)

  if len(parts) > 1:
    parts[-1] = AND.sub('', parts[-1])

  return parts