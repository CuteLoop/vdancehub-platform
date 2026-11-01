from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Movement


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
        ),
        slug=slug,
    )
    return render(request, "knowledge/movement_detail.html", {"movement": movement})
