"""
Base password hashers.

Contains weak hashers (the original ones) available with Modoboa.
"""

from __future__ import unicode_literals

import base64
import crypt
import hashlib
from random import Random
import string

from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_text, force_bytes


class PasswordHasher(object):

    """
    Base class of all hashers.
    """

    def __init__(self, target='local'):
        self._target = target

    def _encrypt(self, clearvalue, salt=None):
        raise NotImplementedError

    def _b64encode(self, pwhash):
        """Encode :keyword:`pwhash` using base64 if needed.

        :param str pwhash: password hash
        :return: base64 encoded hash or original hash
        """
        if self._target == 'ldap':
            return base64.b64encode(pwhash)
        return pwhash

    def encrypt(self, clearvalue):
        """Encrypt a password.

        The format used to store passwords is the same than dovecot's one::

          {SCHEME}<hash>

        <hash> may differ according to the used scheme.

        :param str clearvalue: clear password
        :rtype: str
        :return: encrypted password
        """
        pwhash = self._b64encode(self._encrypt(force_text(clearvalue)))
        return '%s%s' % (self.scheme, force_text(pwhash))

    def verify(self, clearvalue, hashed_value):
        """Verify a password against a hashed value.

        :param str clearvalue: clear password
        :param str hashed_value: password previously hashed
        :return: True if passwords match, False otherwise
        """
        return constant_time_compare(
            self._b64encode(self._encrypt(clearvalue, hashed_value)),
            hashed_value
        )


class PLAINHasher(PasswordHasher):

    """
    Plain (ie. clear) password hasher.
    """
    @property
    def scheme(self):
        return '{PLAIN}'

    def _encrypt(self, clearvalue, salt=None):
        return clearvalue


class CRYPTHasher(PasswordHasher):

    """
    crypt password hasher.

    Uses python `crypt` standard module.
    """
    @property
    def scheme(self):
        return '{CRYPT}'

    def _encrypt(self, clearvalue, salt=None):
        if salt is None:
            salt = "".join(Random().sample(string.ascii_letters + string.digits, 2))
        return crypt.crypt(clearvalue, salt)


class MD5Hasher(PasswordHasher):

    """
    MD5 password hasher.

    Uses python `hashlib` standard module.
    """
    @property
    def scheme(self):
        return '{MD5}'

    def _encrypt(self, clearvalue, salt=None):
        obj = hashlib.md5(force_bytes(clearvalue))
        return obj.hexdigest()


class SHA256Hasher(PasswordHasher):

    """
    SHA256 password hasher.

    Uses python `hashlib` and `base64` standard modules.
    """
    @property
    def scheme(self):
        return '{SHA256}'

    def _encrypt(self, clearvalue, salt=None):
        return hashlib.sha256(force_bytes(clearvalue)).digest()

    def _b64encode(self, pwhash):
        """Encode :keyword:`pwhash` using base64.

        :param str pwhash: password hash
        :return: base64 encoded hash
        """
        return base64.b64encode(pwhash)
