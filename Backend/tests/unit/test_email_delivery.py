"""Sign-up codes: shown on screen without SMTP, e-mail only with it."""

from app.services.email_service import EmailService


def _service(user: str, password: str) -> EmailService:
    service = EmailService()
    service.smtp_user = user
    service.smtp_password = password
    return service


def test_code_is_returned_when_smtp_is_not_configured():
    service = _service("", "")
    assert not service.enabled
    assert service.delivery("123456") == {"email_sent": False, "code": "123456"}


def test_code_is_never_returned_when_smtp_is_configured():
    service = _service("me@example.com", "app-password")
    assert service.enabled
    assert service.delivery("123456") == {"email_sent": True, "code": None}


def test_half_configured_smtp_counts_as_not_configured():
    assert not _service("me@example.com", "").enabled
    assert not _service("", "app-password").enabled
