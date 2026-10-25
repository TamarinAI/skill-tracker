from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("members/", views.members_list, name="members-list"),
    path("members/<str:discord_id>/", views.member_detail, name="member-detail"),
    path("members/<str:discord_id>/points/", views.add_points, name="add-points"),
    path("lessons/<int:lesson_id>/complete/", views.complete_lesson, name="complete-lesson"),
    path("inductions/<int:induction_id>/review/", views.review_induction, name="review-induction"),
]
