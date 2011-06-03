import datetime
from mongoengine import *
from fancyashow.db.models import ShowSet

class User(Document):
    """A User document that aims to mirror most of the API specified by Django
    at http://docs.djangoproject.com/en/dev/topics/auth/#users
    """
    username = StringField(max_length=30, required=True)
    first_name = StringField(max_length=30)
    last_name = StringField(max_length=30)
    email = StringField()
    password = StringField(max_length=128, default = '!')
    is_staff = BooleanField(default=False)
    is_active = BooleanField(default=True)
    is_superuser = BooleanField(default=False)
    last_login = DateTimeField(default=datetime.datetime.now)
    date_joined = DateTimeField(default=datetime.datetime.now)

    def __unicode__(self):
        return self.username

    def get_full_name(self):
        """Returns the users first and last names, separated by a space.
        """
        full_name = u'%s %s' % (self.first_name or '', self.last_name or '')
        return full_name.strip()

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def set_password(self, raw_password):
        """Sets the user's password - always use this rather than directly
        assigning to :attr:`~mongoengine.django.auth.User.password` as the
        password is hashed before storage.
        """
        from random import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random()), str(random()))[:5]
        hash = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hash)
        self.save()
        return self

    def check_password(self, raw_password):
        """Checks the user's password against a provided password - always use
        this rather than directly comparing to
        :attr:`~mongoengine.django.auth.User.password` as the password is
        hashed before storage.
        """
        algo, salt, hash = self.password.split('$')
        return hash == get_hexdigest(algo, salt, raw_password)

    @classmethod
    def create_user(cls, username, password, email=None):
        """Create (and save) a new user with the given username, password and
        email address.
        """
        now = datetime.datetime.now()

        # Normalize the address by lowercasing the domain part of the email
        # address.
        if email is not None:
            try:
                email_name, domain_part = email.strip().split('@', 1)
            except ValueError:
                pass
            else:
                email = '@'.join([email_name, domain_part.lower()])

        user = User(username=username, email=email, date_joined=now)
        user.set_password(password)
        user.save()
        return user

    def get_and_delete_messages(self):
        return []
    
    @property
    def starred_show_set(self):
      if not hasattr(self, '_show_set'):
        show_set_query  = Q(set_type = 'user-starred',  set_context_id = self.id)
        show_set_kwargs = {'set_type': 'user-starred', 'set_context_id': self.id}

        show_set, created = ShowSet.objects.get_or_create(show_set_query, defaults = show_set_kwargs)

        setattr(self, '_show_set', show_set)

      return self._show_set

class AnonymousUser(User):
    def is_anonymous(self):
        return True

    def is_authenticated(self):
        return False
