"""The accounts the local suite signs in with; run by `manage.py shell`."""

import os

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

user = get_user_model().objects.create_user(
    os.environ["APP_TEST_USER"], f"{os.environ['APP_TEST_USER']}@example.com",
    os.environ["APP_TEST_PASSWORD"],
)
EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
print(f"seeded {user.username}")
