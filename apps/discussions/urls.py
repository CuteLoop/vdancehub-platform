from django.urls import path

from . import views

app_name = "discussions"

urlpatterns = [
    path("", views.topic_list, name="list"),
    path("<uuid:pk>/", views.topic_detail, name="detail"),
    path("<uuid:pk>/reply/", views.reply_to_topic, name="reply"),
]
