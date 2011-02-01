import mongoforms

from django               import forms
from mongoforms.fields    import ReferenceField
from fancyashow.db.models import Show

class ShowChoiceForm(forms.Form):
  show = ReferenceField(Show.objects)