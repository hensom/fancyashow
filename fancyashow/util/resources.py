import logging
import re

logger = logging.getLogger(__name__)

def HrefMatcher(node, match_exp):
  for anchor in node.iter(tag = 'a'):
    if anchor.get('href'):
      logger.debug("Found link: %s" % anchor.get('href'))

      m = match_exp.match(anchor.get('href'))

      if m:
        logger.debug("Link matches expression: %s" % anchor.get('href'))

        yield m

def ParamMatcher(node, name, match_exp):
  for param in node.iter(tag = 'param'):
    param_name, param_value = param.get('name'), param.get('value')

    logger.debug("Found param named: %s" % param_name)

    if param_name == name:
      logger.debug("Param name matches requested name: %s, value: %s" % (param_name, param_value))

      m = match_exp.match(param_value)

      if m:
        logger.debug("Param value matches expression: %s" % param_value)

        yield m

def URLMatch(match , http_required = True):
  http_re = 'http[s]?:\/\/'

  if not http_required:
    http_re = '(?:%s)' % http_re

  return re.compile('%s%s' % (http_re, match))