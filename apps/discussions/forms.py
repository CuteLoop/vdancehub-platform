from django import forms
from django.core.exceptions import ValidationError

from apps.knowledge.references import classify_reference_url


class DiscussionReplyForm(forms.Form):
    body = forms.CharField(
        label="Your reply",
        max_length=5000,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": (
                    "Share terminology, technique context, or a constructive correction…"
                ),
            }
        ),
    )
    reference_urls = forms.CharField(
        label="References (optional, one URL per line)",
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "https://www.instagram.com/reel/…/"}
        ),
        help_text="Supported social links are canonicalized. Other HTTPS links require review.",
    )

    def clean_reference_urls(self) -> list[str]:
        urls = [
            line.strip()
            for line in self.cleaned_data["reference_urls"].splitlines()
            if line.strip()
        ]
        if len(urls) > 5:
            raise ValidationError("Add no more than five references per reply.")
        for url in urls:
            classify_reference_url(url)
        return urls
