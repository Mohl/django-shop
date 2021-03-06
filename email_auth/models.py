# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Alternative implementation of Django's authentication User model, which allows to authenticate
against the email field in addition to the username fields.
This alternative implementation is activated by setting ``AUTH_USER_MODEL = 'shop.User'`` in
settings.py, otherwise the default Django or another implementation is used.
"""
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager as BaseUserManager
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    def get_by_natural_key(self, username):
        return self.get(is_active=True, **{self.model.USERNAME_FIELD: username})


@python_2_unicode_compatible
class User(AbstractBaseUser, PermissionsMixin):
    """
    Alternative implementation of Django's User model allowing to authenticate
    against the email field in addition to the username field.
    """
    USERNAME_REGEX = re.compile('^[\w.@+-]+$')

    username = models.CharField(_("Username"), max_length=30, unique=True,
        help_text=_("Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters"),
        validators=[validators.RegexValidator(USERNAME_REGEX, _('Enter a valid username.'), 'invalid')])

    # copied from django.contrib.auth.models.AbstractUser
    first_name = models.CharField(_("First name"), max_length=30, blank=True)
    last_name = models.CharField(_("Last name"), max_length=30, blank=True)

    # this is the only field, which differs from the default implementation
    email = models.EmailField(_("Email address"), null=True, default=None, blank=True, max_length=254)
    is_staff = models.BooleanField(_("staff status"), default=False,
        help_text=_("Designates whether the user can log into this admin site."))
    is_active = models.BooleanField(_("active"), default=True,
        help_text=_("Designates whether this user should be treated as active."
                    "Unselect this instead of deleting accounts."))
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'auth_user'
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")

    def get_username(self):
        if self.is_staff:
            return self.username
        return self.email or '<anonymous>'

    def __str__(self):
        return self.get_username()

    def get_full_name(self):
        full_name = '{} {}'.format(self.first_name, self.last_name)
        full_name = full_name.strip()
        if full_name:
            return full_name
        return self.get_short_name()

    def get_short_name(self):
        if self.first_name:
            return self.first_name
        return self.email

    def email_user(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])

    def validate_unique(self, exclude=None):
        super(User, self).validate_unique(exclude)
        if get_user_model().objects.exclude(id=self.id).filter(is_active=True, email__exact=self.email).exists():
            msg = _("A customer with the e-mail address ‘{email}’ already exists.")
            raise ValidationError({'email': msg.format(email=self.email)})
