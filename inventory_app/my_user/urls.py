from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CreateUserView, LoginView, UpdatePasswordView, CustomUserView, UserActivitiesView, UsersListView
)

router = DefaultRouter(trailing_slash=False)

router.register('create-user', CreateUserView, 'create user')
router.register('login', LoginView, 'login')
router.register('update-password', UpdatePasswordView, 'update password')
router.register('me', CustomUserView, 'me')
router.register('users-activities', UserActivitiesView, 'users activities')
router.register('users-list', UsersListView, 'users list')

urlpatterns = [
    path('', include(router.urls)),
]
