"""Tests for core application."""

from __future__ import unicode_literals

import smtplib

from unittest import skipIf
from mock import patch

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import override_settings

from modoboa.lib.tests import ModoTestCase
from modoboa.lib.tests import NO_SMTP

from .. import factories
from .. import models


class AuthenticationTestCase(ModoTestCase):
    """Validate authentication scenarios."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(AuthenticationTestCase, cls).setUpTestData()
        cls.account = factories.UserFactory(
            username="user@test.com", groups=('SimpleUsers',)
        )

    def test_authentication(self):
        """Validate simple case."""
        self.client.logout()
        data = {"username": "user@test.com", "password": "toto"}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:user_index")))

        response = self.client.post(reverse("core:logout"), {})
        self.assertEqual(response.status_code, 302)

        data = {"username": "admin", "password": "password"}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:dashboard")))

    def test_open_redirect(self):
        """Check that open redirect is not allowed."""
        self.client.logout()
        data = {"username": "admin", "password": "password"}

        # 1. Check valid redirection
        url = "{}?next=/admin/".format(reverse("core:login"))
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("admin:index")))
        self.client.logout()

        # 2. Check bad redirection
        url = "{}?next=http://www.evil.com".format(reverse("core:login"))
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:dashboard")))


class PasswordResetTestCase(ModoTestCase):
    """Test password reset service."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(PasswordResetTestCase, cls).setUpTestData()
        cls.account_ok = factories.UserFactory(
            username="user@test.com", secondary_email="test@ext.com",
            groups=('SimpleUsers',)
        )
        cls.account_ko = factories.UserFactory(
            username="user2@test.com", groups=('SimpleUsers',)
        )

    def test_reset_password(self):
        """Validate simple case."""
        self.client.logout()
        url = reverse("password_reset")
        data = {"email": self.account_ok.email}
        response = self.client.post(url, data, follow=True)
        self.assertContains(
            response,
            "We've emailed you instructions for setting your password")
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_password_no_secondary_email(self):
        """Check email is not sent."""
        self.client.logout()
        url = reverse("password_reset")
        data = {"email": self.account_ko.email}
        response = self.client.post(url, data, follow=True)
        self.assertContains(
            response,
            "We've emailed you instructions for setting your password")
        self.assertEqual(len(mail.outbox), 0)


@skipIf(NO_SMTP, 'No SMTP server available')
@override_settings(AUTHENTICATION_BACKENDS=(
    "modoboa.lib.authbackends.SMTPBackend",
    "django.contrib.auth.backends.ModelBackend"
))
class SMTPAuthenticationTestCase(ModoTestCase):
    """Validate SMTP authentication scenarios."""

    def _test_smtp_authentication(self, mock_smtp):
        """Common code to check authentication"""
        self.client.logout()
        username = "user@unknown.test"
        password = "toto"
        data = {"username": username, "password": password}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:user_index")))
        mock_smtp.return_value.login.assert_called_once_with(
            username, password)
        self.assertTrue(
            models.User.objects.filter(username=username).exists())

    @patch("smtplib.SMTP")
    def test_smtp_authentication(self, mock_smtp):
        """Check simple SMTP authentication."""
        self._test_smtp_authentication(mock_smtp)

    @patch("smtplib.SMTP_SSL")
    @override_settings(AUTH_SMTP_SECURED_MODE="ssl")
    def test_smtp_authentication_over_ssl(self, mock_smtp):
        """Check SMTP authentication over SSL."""
        self._test_smtp_authentication(mock_smtp)

    @patch("smtplib.SMTP")
    @override_settings(AUTH_SMTP_SECURED_MODE="starttls")
    def test_smtp_authentication_over_starttls(self, mock_smtp):
        """Check SMTP authentication over STARTTLS."""
        self._test_smtp_authentication(mock_smtp)

    @patch("smtplib.SMTP")
    def test_smtp_authentication_failure(self, mock_smtp):
        """Check SMTP authentication failure."""
        instance = mock_smtp.return_value
        instance.login.side_effect = smtplib.SMTPAuthenticationError(
            450, "User not found")
        self.client.logout()
        username = "user@unknown.test"
        password = "toto"
        data = {"username": username, "password": password}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 401)
        mock_smtp.return_value.login.assert_called_once_with(
            username, password)
        self.assertFalse(
            models.User.objects.filter(username=username).exists())
