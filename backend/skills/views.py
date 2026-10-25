from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .models import (
    Induction,
    InductionType,
    Lesson,
    LessonCompletion,
    Member,
    PointsEntry,
    SkillRating,
)


def _member_payload(member: Member) -> dict:
    rating = SkillRating.objects.filter(member=member).first()
    total = sum((e.points for e in member.points_entries.all()), start=0)
    return {
        "discord_id": member.discord_id,
        "display_name": member.display_name or member.discord_username,
        "skills": rating.as_dict() if rating else {axis: 0 for axis in SkillRating.AXES},
        "points_total": str(total),
        "inductions": [
            {"type": i.induction_type.name, "status": i.status}
            for i in member.inductions.select_related("induction_type")
        ],
        "lessons_completed": member.lesson_completions.count(),
    }


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_GET
def member_detail(request, discord_id: str):
    member = Member.objects.filter(discord_id=discord_id).first()
    if not member:
        return JsonResponse({"error": "member not found"}, status=404)
    return JsonResponse(_member_payload(member))


@require_GET
def members_list(request):
    days = int(request.GET.get("days", 365))
    members = Member.objects.all()
    return JsonResponse({"members": [_member_payload(m) for m in members]})


@require_POST
def add_points(request, discord_id: str):
    """Award points to a member (lesson, action item, manual)."""
    import json
    from datetime import date

    member = Member.objects.filter(discord_id=discord_id).first()
    if not member:
        return JsonResponse({"error": "member not found"}, status=404)
    body = json.loads(request.body or b"{}")
    try:
        points = float(body.get("points", 0))
    except (TypeError, ValueError):
        return JsonResponse({"error": "points must be numeric"}, status=400)
    source = body.get("source", PointsEntry.SOURCE_MANUAL)
    if source not in dict(PointsEntry.SOURCE_CHOICES):
        return JsonResponse({"error": f"unknown source: {source}"}, status=400)
    if points <= 0:
        return JsonResponse({"error": "points must be positive"}, status=400)
    entry = PointsEntry.objects.create(
        member=member,
        source=source,
        points=points,
        description=str(body.get("description", ""))[:300],
        earned_on=body.get("earned_on") or date.today().isoformat(),
        external_ref=body.get("external_ref") or None,
        logged_by=request.caller_member,
    )
    return JsonResponse({"id": entry.id, "points": str(entry.points)}, status=201)


@require_POST
def complete_lesson(request, lesson_id: int):
    """Mark a lesson complete for the caller member; awards points if quiz passed
    and any required induction is approved."""
    import json

    lesson = Lesson.objects.filter(pk=lesson_id, published=True).first()
    if not lesson:
        return JsonResponse({"error": "lesson not found"}, status=404)
    caller = request.caller_member
    if not caller:
        return JsonResponse({"error": "X-Caller-Member header required"}, status=400)
    if lesson.requires_induction_id:
        ok = Induction.objects.filter(
            member=caller, induction_type_id=lesson.requires_induction_id,
            status=Induction.STATUS_APPROVED,
        ).exists()
        if not ok:
            return JsonResponse(
                {"error": f"induction required: {lesson.requires_induction.name}"}, status=403
            )
    body = json.loads(request.body or b"{}")
    quiz_score = body.get("quiz_score")
    quiz = getattr(lesson, "quiz", None)
    if quiz is not None:
        if quiz_score is None or int(quiz_score) < quiz.pass_mark:
            return JsonResponse({"error": "quiz not passed"}, status=400)
    completion, created = LessonCompletion.objects.get_or_create(
        member=caller, lesson=lesson,
        defaults={"quiz_score": quiz_score, "points_awarded": lesson.points},
    )
    if not created:
        return JsonResponse({"error": "already completed"}, status=409)
    if lesson.points:
        PointsEntry.objects.create(
            member=caller, source=PointsEntry.SOURCE_LESSON, points=lesson.points,
            description=f"Completed lesson: {lesson.title}",
            earned_on=completion.completed_at.date().isoformat(),
            external_ref=f"lesson:{lesson.id}:{caller.id}",
        )
    return JsonResponse({"completed": True, "points_awarded": str(lesson.points)}, status=201)


@require_http_methods(["PATCH"])
def review_induction(request, induction_id: int):
    """Admin approves/rejects a pending induction."""
    import json

    if not request.caller_member or not request.caller_member.is_admin:
        return JsonResponse({"error": "admin only"}, status=403)
    body = json.loads(request.body or b"{}")
    status = body.get("status")
    if status not in (Induction.STATUS_APPROVED, Induction.STATUS_REJECTED):
        return JsonResponse({"error": "status must be approved or rejected"}, status=400)
    induction = Induction.objects.filter(pk=induction_id).first()
    if not induction:
        return JsonResponse({"error": "induction not found"}, status=404)
    from django.utils import timezone

    induction.status = status
    induction.reviewed_at = timezone.now()
    induction.reviewed_by = request.caller_member
    induction.notes = str(body.get("notes", ""))
    induction.save()
    return JsonResponse({"id": induction.id, "status": induction.status})
