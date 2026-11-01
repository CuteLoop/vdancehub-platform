from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.knowledge.services import attach_post_references

from .forms import DiscussionReplyForm
from .models import DiscussionTopic
from .services import create_reply


def topic_list(request: HttpRequest) -> HttpResponse:
    topics: QuerySet[DiscussionTopic] = (
        DiscussionTopic.objects.filter(is_removed=False)
        .select_related("author")
        .prefetch_related("dance_styles", "tags")
        .annotate(reply_count=Count("posts") - 1)
    )
    selected_style = request.GET.get("style", "")
    selected_tag = request.GET.get("tag", "")
    if selected_style:
        topics = topics.filter(dance_styles__slug=selected_style)
    if selected_tag:
        topics = topics.filter(tags__slug=selected_tag)
    return render(
        request,
        "discussions/list.html",
        {
            "topics": topics.distinct(),
            "selected_style": selected_style,
            "selected_tag": selected_tag,
        },
    )


def topic_detail(request: HttpRequest, pk: str) -> HttpResponse:
    topic = get_object_or_404(
        DiscussionTopic.objects.select_related("author").prefetch_related(
            "posts__author", "posts__citations__reference", "dance_styles", "tags"
        ),
        pk=pk,
        is_removed=False,
    )
    return render(
        request,
        "discussions/detail.html",
        {"topic": topic, "reply_form": DiscussionReplyForm()},
    )


@login_required
def reply_to_topic(request: HttpRequest, pk: str) -> HttpResponse:
    if request.method != "POST":
        raise Http404
    assert isinstance(request.user, User)
    topic = get_object_or_404(DiscussionTopic, pk=pk, is_removed=False)
    if request.user.adult_confirmed_at is None or topic.is_closed:
        raise PermissionDenied
    form = DiscussionReplyForm(request.POST)
    if form.is_valid():
        post = create_reply(topic=topic, author=request.user, body=form.cleaned_data["body"])
        attach_post_references(
            post=post,
            urls=form.cleaned_data["reference_urls"],
            author=request.user,
        )
        return redirect("discussions:detail", pk=topic.pk)
    return render(
        request,
        "discussions/detail.html",
        {"topic": topic, "reply_form": form},
        status=400,
    )
