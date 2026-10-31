from django import forms
from django.utils import timezone

from .models import User


class SignupForm(forms.Form):
    display_name = forms.CharField(max_length=80, label="Public display name")
    adult_confirmation = forms.BooleanField(label="I confirm that I am at least 18 years old.")

    def signup(self, request: object, user: User) -> User:
        user.display_name = self.cleaned_data["display_name"]
        user.adult_confirmed_at = timezone.now()
        user.save(update_fields=["display_name", "adult_confirmed_at"])
        return user
