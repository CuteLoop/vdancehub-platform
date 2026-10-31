from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.mediarefs.models import VideoReference

from .models import FeedbackRequest

User = get_user_model()


class FeedbackRequestCreateForm(forms.Form):
    video_url = forms.URLField(max_length=2048, assume_scheme="https")
    attribution_name = forms.CharField(max_length=160)
    video_description = forms.CharField(widget=forms.Textarea)
    title = forms.CharField(max_length=180)
    goals = forms.CharField(widget=forms.Textarea)
    dancer_role = forms.ChoiceField(choices=FeedbackRequest.DancerRole.choices)
    skill_level = forms.ChoiceField(choices=FeedbackRequest.SkillLevel.choices)
    footage_consent_confirmed = forms.BooleanField()
    adults_only_confirmed = forms.BooleanField()
    constructive_guidelines_accepted = forms.BooleanField()

    @transaction.atomic
    def save(self, *, author: User) -> FeedbackRequest:  # type: ignore[valid-type]
        video = VideoReference.objects.create(
            owner=author,
            submitted_url=self.cleaned_data["video_url"],
            attribution_name=self.cleaned_data["attribution_name"],
            description=self.cleaned_data["video_description"],
        )
        return FeedbackRequest.objects.create(
            author=author,
            video=video,
            title=self.cleaned_data["title"],
            goals=self.cleaned_data["goals"],
            dancer_role=self.cleaned_data["dancer_role"],
            skill_level=self.cleaned_data["skill_level"],
            footage_consent_confirmed=self.cleaned_data["footage_consent_confirmed"],
            adults_only_confirmed=self.cleaned_data["adults_only_confirmed"],
            constructive_guidelines_accepted=self.cleaned_data["constructive_guidelines_accepted"],
        )
