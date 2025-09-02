from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from functools import wraps

superuser_required = user_passes_test(
    lambda u: u.is_authenticated and u.is_superuser,
    login_url='/admin/login/'
)