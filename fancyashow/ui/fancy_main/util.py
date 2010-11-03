import logging
import os
import errno
import os.path
from django.conf      import settings

def init_logging(log_type, start_time):
  log_dir = os.path.join(settings.COMMAND_LOG_DIR, log_type)

  try:
     os.makedirs(log_dir)
  except OSError, exc: # Python >2.5
    if exc.errno == errno.EEXIST:
      pass
    else:
      raise

  handler = logging.FileHandler(os.path.join(log_dir, '%s.log' % start_time.strftime('%s')))
  
  formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

  handler.setFormatter(formatter)
  
  logging.getLogger().addHandler(handler)
