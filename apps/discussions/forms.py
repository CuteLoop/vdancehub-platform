from django import forms


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
