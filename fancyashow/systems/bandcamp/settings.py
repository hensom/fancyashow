from django.conf              import settings
from fancyashow.util.settings import get_required_setting

API_KEY = get_required_setting(settings, 'BANDCAMP_API_KEY')
