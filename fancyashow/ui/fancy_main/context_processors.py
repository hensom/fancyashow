from django.conf import settings

def site_info(request):
  return {'SITE_NAME': settings.SITE_NAME, 'SITE_TAGLINE': settings.SITE_TAGLINE}

def analytics(request):
  return {'GOOGLE_ANALYTICS_ACCOUNT': settings.GOOGLE_ANALYTICS_ACCOUNT}