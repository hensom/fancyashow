def get_setting(settings, attribute_name, default):
  return getattr(settings, attribute_name, default)

def get_required_setting(settings, attribute_name):
  ret = get_setting(settings, attribute_name, None)

  if not ret:
    raise Exception('%s must be specified in settings.py' % attribute_name)
  else:
    return ret
