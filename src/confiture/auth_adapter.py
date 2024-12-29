from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

from core.models import Profile


class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        profile = Profile.objects.filter(user=request.user).first()
        print(profile)
        return reverse("core:org-detail", args=(profile.organization_id,))
