import re
import mongoengine
from mongoengine.base import ValidationError

ALL_SPACES = re.compile('^\s*$')

class StringField(mongoengine.StringField):
  def validate(self, value):
    super(StringField, self).validate(value)

    if self.required and (not value or ALL_SPACES.match(value)):
      raise ValidationError('Field "%s" is required and must not be empty' % self.name)