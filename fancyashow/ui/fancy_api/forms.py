import mongoforms

from django               import forms
from mongoforms.fields    import ReferenceField
from fancyashow.db.models import Show

class SavedShowsForm(forms.Form):
  add    = ReferenceField(Show.objects(), required = False)
  remove = ReferenceField(Show.objects(), required = False)
