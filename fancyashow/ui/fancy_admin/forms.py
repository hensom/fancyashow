from datetime                 import datetime
from django                   import forms
from django.utils.translation import ugettext
from fancyashow.util          import lang
from fancyashow.db.models     import Artist, ArtistProfile

def initial_for_instance(form, instance):
  initial = { }

  for f in form.base_fields:
    initial[f] = getattr(instance, f)

  return initial
  
class ModelForm(forms.Form):
  def __init__(self, *args, **kwargs):
    self.instance = kwargs.pop('instance', None)

    if self.instance:
      initial = initial_for_instance(self, self.instance)

      initial.update(kwargs.get('initial', {}))

      kwargs['initial'] = initial

    super(ModelForm, self).__init__(*args, **kwargs)
  
class ResourceInput(forms.Textarea):
  def render(self, name, value, attrs=None):
    if isinstance(value, list):
      value = '\n'.join(value)
      
    return super(ResourceInput, self).render(name, value, attrs)
  
class ResourceField(forms.CharField):
  def __init__(self, *args, **kwargs):
    if 'widget' not in kwargs:
      kwargs['widget'] = ResourceInput
      
    super(ResourceField, self).__init__(self, *args, **kwargs)

  def clean(self, value):
    values = []

    for val in value.split('\n'):
      val = val.strip()
      
      if val:
        values.append(val)
        
    if self.required and len(values) == 0:
        raise ValidationError(self.error_messages['required'])
        
    return values
  
class BooleanSelect(forms.RadioSelect):
  def __init__(self, attrs=None):
      choices = ((u'1', ugettext('Yes')), (u'2', ugettext('No')))
      super(BooleanSelect, self).__init__(attrs, choices)

  def render(self, name, value, attrs=None, choices=()):
    try:
      value = {True: u'1', False: u'2', u'1': u'1', u'2': u'2'}[value]
    except KeyError:
      value = False

    return super(BooleanSelect, self).render(name, value, attrs, choices)

  def value_from_datadict(self, data, files, name):
      value = data.get(name, None)
      return {u'1': True,
              True: True,
              'True': True,
              u'2': False,
              'False': False,
              False: False}.get(value, None)
              
class OverrideInput(forms.CheckboxInput):
  def __init__(self, *args, **kwargs):
    if 'attrs' not in kwargs:
      kwargs['attrs'] = { }
      
    if 'size' not in kwargs['attrs']:
      kwargs['attrs']['class'] = 'override'

    super(OverrideInput, self).__init__(*args, **kwargs)

class BasicTextInput(forms.TextInput):
  def __init__(self, *args, **kwargs):
    if 'attrs' not in kwargs:
      kwargs['attrs'] = { }
      
    if 'size' not in kwargs['attrs']:
      kwargs['attrs']['size'] = 50

    super(BasicTextInput, self).__init__(*args, **kwargs)

class URLInput(forms.TextInput):
  def __init__(self, *args, **kwargs):
    if 'attrs' not in kwargs:
      kwargs['attrs'] = { }
      
    if 'size' not in kwargs['attrs']:
      kwargs['attrs']['size'] = 100

    super(URLInput, self).__init__(*args, **kwargs)
  
RANGE_CHOICES    = (
  ('on',     'On'),
  ('before', 'Before'),
  ('after',  'After')
)

RESTRICT_CHOICES = (
  ('any',             'All Shows'),
  ('no_headliner',    'No Headliner'),
  ('handling_failed', 'Handling Failed'),
  ('not_handled',     'Not Handled')
)
  
class AdminShowFilterForm(forms.Form):
  query      = forms.CharField(required = False)
  show_range = forms.ChoiceField(label = 'Show Date Was', choices = RANGE_CHOICES, initial = 'on')
  show_date  = forms.DateField(required = True, label = 'Date', initial = lambda: datetime.now().date())
  no_image   = forms.BooleanField(label = 'Without Image', required = False)
  is_hidden  = forms.BooleanField(label = 'Hidden', required = False)
  restrict   = forms.ChoiceField(label = 'Restrict', choices = RESTRICT_CHOICES, required = False)
  resource   = forms.CharField(required = False)
  
class AdminArtistFilterForm(forms.Form):
  query = forms.CharField(required = False)
  suspect = forms.BooleanField(label = 'Name is Suspect', required = False)
  
class ShowVenueForm(forms.Form):
  name = forms.CharField(widget = BasicTextInput)
  url  = forms.CharField(widget = URLInput)
  
class ArtistInfoForm(ModelForm):
  name       = forms.CharField(widget = BasicTextInput, required = False)
  headliner  = forms.BooleanField(required = False)
  start_time = forms.CharField(required = False)
  
  def clean(self):
    data      = self.cleaned_data
    have_name = data.get('name', '').strip() != ''
    
    if not have_name:
      for f in self.base_fields:
        val = self.cleaned_data.get(f)

        if f != 'name' and val not in (None, False, ''):
          raise forms.ValidationError('Please enter a name')

    return data

class ShowForm(forms.Form):
  title            = forms.CharField(widget = BasicTextInput, required = False)
  date             = forms.DateTimeField()
  show_time        = forms.DateTimeField(required = False)
  door_time        = forms.DateTimeField(required = False)    
  soldout          = forms.BooleanField(widget = BooleanSelect, required = False)
  url              = forms.URLField(widget = URLInput, required = False)
  image_url        = forms.URLField(widget = URLInput, required = False)
  parsed_resources = ResourceField(required = False)
  visible          = forms.BooleanField(widget = BooleanSelect, required = False, label = 'Shown')
  
class ArtistAssociationForm(forms.Form):
  show_id         = forms.CharField(required = False)
  artist_position = forms.IntegerField(required = False)
  
  def clean(self):
    have_show_id = self.cleaned_data.get('show_id')
    have_artist  = self.cleaned_data.get('artist_position') is not None

    if have_show_id and not have_artist:
      raise forms.ValidationError('artist_position must be defined if show_id is passed in')
    elif have_artist and not have_show_id:
      raise forms.ValidationError('show_id must be defined if artist_position is passed in')

    return self.cleaned_data

class ArtistForm(ModelForm):
  name = forms.CharField(required = True)
  
  def clean_name(self):
    name = self.cleaned_data['name']
    
    if Artist.objects(normalized_name = lang.normalize(name)).count() > 0:
      raise forms.ValidationError('Another artist with this name already exists')

    return name

  def save(self):
    artist = self.instance
    
    if artist:
      artist.name            = self.cleaned_data['name']
      # FIXME handle this as an override to save perhaps?
      artist.normalized_name = lang.normalize(self.cleaned_data['name'])
    else:
      artist = Artist(name = self.cleaned_data['name'], normalized_name = lang.normalize(self.cleaned_data['name']))
      
    return artist
  
class ArtistStateForm(forms.Form):
  num_profiles = forms.IntegerField(required = True)

class ProfileForm(ModelForm):
  system_id     = forms.CharField(widget = forms.TextInput(attrs = {'size': 100 }), required = False)
  profile_id    = forms.CharField(widget = forms.TextInput(attrs = {'size': 100 }), required = False)
  url           = forms.URLField(widget = forms.TextInput(attrs = {'size': 100 }),  required = False)
  
  def __init__(self, source_id, *args, **kwargs):
    super(ProfileForm, self).__init__(*args, **kwargs)

    self.source_id = source_id
  
  def defined(self):
    for field in self.fields.keys():
      if not self.cleaned_data.get(field):
        return False

    return True

  def clean(self):
    empty       = 0
    filled      = 0
    empty_field = None
    
    for field in self.fields.keys():
      if self.cleaned_data.get(field):
        filled += 1
      else:
        empty += 1
        empty_field = field

    if filled > 0 and empty > 0:
      raise forms.ValidationError('%s must be defined' % empty_field)

    return self.cleaned_data
    
  def save(self):
    profile = self.instance

    if self.instance:
      profile.system_id  = self.cleaned_data['system_id']
      profile.profile_id = self.cleaned_data['profile_id']
      profile.url        = self.cleaned_data['url']
    else:
      profile_args = {
        'system_id':  self.cleaned_data['system_id'],
        'profile_id': self.cleaned_data['profile_id'],
        'url':        self.cleaned_data['url'],
        'source_id':  self.source_id
      }

      profile = ArtistProfile(**profile_args)
      
    return profile