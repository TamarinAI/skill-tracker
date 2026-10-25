"""Bearer-token auth for server-to-server calls (discordbot, Tamarin, training site).

Sets request.caller_member from the X-Caller-Member discord id when the shared
SKILL_TRACKER_TOKEN matches. Health endpoint stays open.
"""
from django.conf import settings
from django.http import JsonResponse

from .models import Member


class ApiTokenMiddleware:
    OPEN_PATHS = ("/api/health/",)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.caller_member = None
        if request.path.startswith("/api/") and not request.path.startswith(self.OPEN_PATHS):
            expected = settings.SKILL_TRACKER_TOKEN
            supplied = ""
            header = request.headers.get("Authorization", "")
            if header.startswith("Bearer "):
                supplied = header[7:]
            if not expected or supplied != expected:
                return JsonResponse({"error": "unauthorized"}, status=401)
            caller_id = request.headers.get("X-Caller-Member", "")
            if caller_id:
                request.caller_member = Member.objects.filter(discord_id=caller_id).first()
        return self.get_response(request)
