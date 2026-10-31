from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User

from .forms import FeedbackRequestCreateForm
from .models import FeedbackRequest


@login_required
def create_feedback_request(request: HttpRequest) -> HttpResponse:
    assert isinstance(request.user, User)
    if request.user.adult_confirmed_at is None:
        raise PermissionDenied("Adult confirmation is required.")
    form = FeedbackRequestCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            feedback_request = form.save(author=request.user)
        except ValidationError as exc:
            form.add_error("video_url", exc)
        else:
            return redirect("feedback:detail", pk=feedback_request.pk)
    return render(request, "feedback/create.html", {"form": form})


def feedback_request_detail(request: HttpRequest, pk: str) -> HttpResponse:
    feedback_request = get_object_or_404(
        FeedbackRequest.objects.select_related("video", "author"), pk=pk
    )
    if not feedback_request.video.can_view(request.user, via_direct_link=True):
        raise Http404
    return render(request, "feedback/detail.html", {"feedback_request": feedback_request})
