from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.discussions.forms import DiscussionReplyForm
from apps.discussions.models import DiscussionTopic
from apps.discussions.services import create_reply

from .models import Curriculum, KnowledgePage, Movement, MovementRelationship, ReviewedEdition
from .services import attach_post_references


def curriculum_list(request: HttpRequest) -> HttpResponse:
    curricula = Curriculum.objects.select_related("dance_style", "source").prefetch_related(
        "versions__modules__concept_entries"
    )
    return render(request, "knowledge/curriculum_list.html", {"curricula": curricula})


def curriculum_detail(request: HttpRequest, slug: str) -> HttpResponse:
    curriculum = get_object_or_404(
        Curriculum.objects.select_related(
            "dance_style", "source", "discussion__native_topic"
        ).prefetch_related(
            "versions__modules__concept_entries__concept__dance_style",
            "versions__modules__concept_entries__concept__living_page",
            "versions__modules__concept_entries__concept__outgoing_relationships__to_movement",
        ),
        slug=slug,
    )
    return render(request, "knowledge/curriculum_detail.html", {"curriculum": curriculum})


def _curriculum_with_topic(slug: str) -> tuple[Curriculum, DiscussionTopic]:
    curriculum = get_object_or_404(
        Curriculum.objects.select_related("dance_style", "discussion__native_topic"), slug=slug
    )
    if curriculum.discussion is None or curriculum.discussion.native_topic is None:
        raise Http404
    topic = get_object_or_404(
        DiscussionTopic.objects.select_related("author").prefetch_related(
            "posts__author", "posts__citations__reference", "dance_styles", "tags"
        ),
        pk=curriculum.discussion.native_topic.pk,
        is_removed=False,
    )
    return curriculum, topic


def curriculum_discussion(request: HttpRequest, slug: str) -> HttpResponse:
    curriculum, topic = _curriculum_with_topic(slug)
    return render(
        request,
        "discussions/detail.html",
        {"curriculum": curriculum, "topic": topic, "reply_form": DiscussionReplyForm()},
    )


@login_required
def reply_to_curriculum_discussion(request: HttpRequest, slug: str) -> HttpResponse:
    if request.method != "POST":
        raise Http404
    assert isinstance(request.user, User)
    curriculum, topic = _curriculum_with_topic(slug)
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
        return redirect("knowledge:curriculum-discussion", slug=curriculum.slug)
    return render(
        request,
        "discussions/detail.html",
        {"curriculum": curriculum, "topic": topic, "reply_form": form},
        status=400,
    )


def page_detail(request: HttpRequest, slug: str) -> HttpResponse:
    page = get_object_or_404(
        KnowledgePage.objects.filter(is_published=True)
        .select_related("owner", "movement")
        .prefetch_related(
            "contributors",
            "dance_styles",
            "references",
            "linked_discussions__native_topic",
            "reviewed_editions",
            "revisions",
        ),
        slug=slug,
    )
    return render(request, "knowledge/page_detail.html", {"page": page})


def edition_detail(request: HttpRequest, slug: str, edition_number: int) -> HttpResponse:
    edition = get_object_or_404(
        ReviewedEdition.objects.select_related("page", "source_revision").prefetch_related(
            "reviewed_by"
        ),
        page__slug=slug,
        page__is_published=True,
        edition_number=edition_number,
    )
    return render(request, "knowledge/edition_detail.html", {"edition": edition})


def graph(request: HttpRequest) -> HttpResponse:
    concepts = (
        Movement.objects.filter(is_concept=True, module_appearances__isnull=False)
        .select_related("dance_style")
        .prefetch_related("living_page", "module_appearances__module__version__curriculum")
        .distinct()
        .order_by("dance_style__name", "name")
    )
    relationships = (
        MovementRelationship.objects.filter(
            from_movement__module_appearances__isnull=False,
            to_movement__module_appearances__isnull=False,
        )
        .select_related("from_movement", "to_movement")
        .distinct()[:80]
    )
    return render(
        request,
        "knowledge/graph.html",
        {"concepts": concepts, "relationships": relationships},
    )


def movement_list(request: HttpRequest) -> HttpResponse:
    movements = Movement.objects.select_related("dance_style", "discussion").prefetch_related(
        "tags", "name_aliases"
    )
    difficulty = request.GET.get("difficulty", "")
    category = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()
    if difficulty.isdigit():
        movements = movements.filter(difficulty=int(difficulty), is_concept=False)
    if category:
        movements = movements.filter(tags__slug=category)
    if query:
        movements = movements.filter(
            Q(name__icontains=query) | Q(name_aliases__name__icontains=query)
        )
    return render(
        request,
        "knowledge/movement_list.html",
        {
            "movements": movements.distinct(),
            "difficulty": difficulty,
            "category": category,
            "query": query,
        },
    )


def movement_detail(request: HttpRequest, slug: str) -> HttpResponse:
    movement = get_object_or_404(
        Movement.objects.select_related("dance_style", "discussion__native_topic").prefetch_related(
            "tags",
            "name_aliases",
            "references",
            "outgoing_relationships__to_movement",
            "incoming_relationships__from_movement",
            "module_appearances__module__version__curriculum",
        ),
        slug=slug,
    )
    return render(request, "knowledge/movement_detail.html", {"movement": movement})
