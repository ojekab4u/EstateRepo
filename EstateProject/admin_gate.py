"""Redirect authenticated non-staff users away from the admin area with a
clear message instead of Django's default 'not authorized' page."""
from django.contrib import messages
from django.shortcuts import redirect

ADMIN_PATH = "/comfy-home-ad-mi-n/"


class AdminGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.path.startswith(ADMIN_PATH)
                and request.user.is_authenticated
                and not request.user.is_staff):
            messages.info(request, "This area is for administrators only.")
            return redirect("index")
        return self.get_response(request)
