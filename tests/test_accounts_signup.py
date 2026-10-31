import pytest
from django.utils import timezone

from apps.accounts.forms import SignupForm
from apps.accounts.models import User


@pytest.mark.django_db
def test_signup_form_records_display_name_and_adult_confirmation() -> None:
    form = SignupForm(data={"display_name": "Dance Friend", "adult_confirmation": True})
    assert form.is_valid()
    user = User(email="friend@example.com")
    form.signup(object(), user)
    assert user.display_name == "Dance Friend"
    assert user.adult_confirmed_at is not None
    assert user.adult_confirmed_at <= timezone.now()


def test_signup_form_rejects_missing_adult_confirmation() -> None:
    form = SignupForm(data={"display_name": "Dance Friend"})
    assert not form.is_valid()
    assert "adult_confirmation" in form.errors
