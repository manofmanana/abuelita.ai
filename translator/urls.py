from django.urls import path
from . import views

app_name = "translator"

urlpatterns = [
    path("", views.home, name="index"),
    path("learn/", views.learn, name="learn"),
    path("about/", views.about, name="about"),
    path("health/", views.health, name="health"),
    # LMS/OOAPI integrations removed
    path("speak/", views.speak_api, name="speak_api"),
    path("save-lesson/", views.save_lesson, name="save_lesson"),
    path("recommend/", views.recommend, name="recommend"),
    # Development helper to clear language cookie
    path("clear-cookies/", views.clear_cookies, name="clear_cookies"),
    path("download-translated/<str:uid>/", views.download_translated, name="download_translated"),
]
