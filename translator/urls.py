from django.urls import path

from . import views

app_name = "translator"

urlpatterns = [
    path("", views.home, name="index"),
    path("learn/", views.learn, name="learn"),
    path("about/", views.about, name="about"),
    path("health/", views.health, name="health"),
    path("save-lesson/", views.save_lesson, name="save_lesson"),
    path("recommend/", views.recommend, name="recommend"),
    path("download-translated/<str:uid>/", views.download_translated, name="download_translated"),
]
