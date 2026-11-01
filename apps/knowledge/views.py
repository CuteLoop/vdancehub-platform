from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Curriculum, Movement, MovementRelationship


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
            "versions__modules__concept_entries__concept__outgoing_relationships__to_movement",
        ),
        slug=slug,
    )
    return render(request, "knowledge/curriculum_detail.html", {"curriculum": curriculum})


def graph(request: HttpRequest) -> HttpResponse:
    concepts = (
        Movement.objects.filter(is_concept=True, module_appearances__isnull=False)
        .select_related("dance_style")
        .prefetch_related("module_appearances__module__version__curriculum")
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
