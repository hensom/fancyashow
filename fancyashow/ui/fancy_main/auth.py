import facebook
import urllib
from django.conf                     import settings
from django.contrib                  import auth
from django.core.urlresolvers        import reverse
from django.http                     import HttpResponseRedirect, HttpResponseServerError, HttpResponse
from fancyashow.ui.fancy_main.models import User

# FacebookBacked borrowed and modified with love from:
# https://github.com/agiliq/Django-Socialauth/blob/master/socialauth/auth_backends.py
class FacebookBackend:
    def authenticate(self, request):
        user = None
        cookie = facebook.get_user_from_cookie(request.COOKIES,
                                               settings.FACEBOOK_APP_ID,
                                               settings.FACEBOOK_SECRET_KEY)
        if cookie:
            uid = cookie['uid']
            access_token = cookie['access_token']
        else:
            # if cookie does not exist
            # assume logging in normal way
            params = {}
            params["client_id"] = settings.FACEBOOK_APP_ID
            params["client_secret"] = settings.FACEBOOK_SECRET_KEY
            params["redirect_uri"] = '%s://%s%s' % (
                         'https' if request.is_secure() else 'http',
                         settings.DOMAIN,
                         reverse("root"))
            params["code"] = request.GET.get('code', '')

            url = ("https://graph.facebook.com/oauth/access_token?"
                   + urllib.urlencode(params))
            from cgi import parse_qs
            userdata = urllib.urlopen(url).read()
            res_parse_qs = parse_qs(userdata)
            # Could be a bot query
            if not res_parse_qs.has_key('access_token'):
                return None
                
            access_token = res_parse_qs['access_token'][-1]
            
            graph = facebook.GraphAPI(access_token)
            uid = graph.get_object('me')['id']
            
        try:
            return User.objects.get(username=uid)
        except User.DoesNotExist:
            # create new FacebookUserProfile
            graph = facebook.GraphAPI(access_token) 
            fb_data = graph.get_object("me")

            if not fb_data:
                return None

            if not user:
                user = User.objects.create(username=uid)
                user.first_name = fb_data['first_name']
                user.last_name  = fb_data['last_name']
                user.save()
                
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None

def login(request):
    user = auth.authenticate(request=request)

    if not user:
        request.COOKIES.pop(settings.FACEBOOK_API_KEY + '_session_key', None)
        request.COOKIES.pop(settings.FACEBOOK_API_KEY + '_user', None)

        return HttpResponseServerError()

    auth.login(request, user)
    
    return HttpResponse()
    
def logout(request):
    auth.logout(request)
    
    response = HttpResponse()
    
    response.delete_cookie("fbs_" + settings.FACEBOOK_APP_ID)
    
    return response