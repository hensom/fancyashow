from fancyashow.ui.fancy_setup.settings import *

from local_settings import *

if LOG_ENABLED:
  logger = logging.getLogger()

  logger.setLevel(LOG_LEVEL)

  if isinstance(LOG_FILE, basestring):
    handler = logging.FileHandler(LOG_FILE)
  else:
    handler = logging.StreamHandler(LOG_FILE)

  handler.setFormatter(logging.Formatter(LOG_FORMAT))

  logger.addHandler(handler)
