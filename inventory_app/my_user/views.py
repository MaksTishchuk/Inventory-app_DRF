from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from django.contrib.auth import authenticate
from datetime import datetime

from .serializers import (
    CreateUserSerializer, LoginSerializer, UpdatePasswordSerializer, CustomUserSerializer,
    UserActivitiesSerializer
)
from .models import CustomUser, UserActivities
from .utils import get_access_token, add_user_activities
from .permissions import IsAuthenticatedCustom


class CreateUserView(ModelViewSet):
    """ Представление для создания пользователя """

    http_method_names = ['get']
    queryset = CustomUser.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = [IsAuthenticatedCustom]

    def create(self, request, *args, **kwargs):
        valid_request = self.serializer_class(data=request.data)
        valid_request.is_valid(raise_exception=True)

        CustomUser.objects.create(**valid_request.validated_data)

        add_user_activities(request.user, 'added new user')

        return Response(
            {'success': 'User created successfully!'},
            status=status.HTTP_201_CREATED
        )


class LoginView(ModelViewSet):
    """ Представление для входа """

    http_method_names = ['post']
    queryset = CustomUser.objects.all()
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        valid_request = self.serializer_class(data=request.data)
        valid_request.is_valid(raise_exception=True)

        new_user = valid_request.validated_data['is_new_user']

        if new_user:
            user = CustomUser.objects.filter(
                email=valid_request.validated_data['email']
            )

            if user:
                user = user[0]
                if not user.password:
                    return Response({'user_id': user.id})
                else:
                    raise Exception('User has password already!')
            else:
                raise Exception('User with this email not found!')

        user = authenticate(
            username=valid_request.validated_data['email'],
            password=valid_request.validated_data.get('password', None)
        )
        if not user:
            return Response(
                {'error': 'Invalid email or password!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        access = get_access_token({'user_id': user.id}, 1)
        user.last_login = datetime.now()
        user.save()

        add_user_activities(user, 'logged in')

        return Response({'access': access})


class UpdatePasswordView(ModelViewSet):
    """ Предствление для обновления пароля пользователя """

    http_method_names = ['post']
    serializer_class = UpdatePasswordSerializer
    queryset = CustomUser.objects.all()

    def create(self, request, *args, **kwargs):
        valid_request = self.serializer_class(data=request.data)
        valid_request.is_valid(raise_exception=True)

        user = CustomUser.objects.filter(id=valid_request.validated_data['user_id'])
        if not user:
            raise Exception('User with thi id not found!')
        user = user[0]
        user.set_password(valid_request.validated_data['password'])
        user.save()

        add_user_activities(user, 'updated password')

        return Response({'success': 'User password updated!'})


class CustomUserView(ModelViewSet):
    """ Представление для получения информации про пользователя """

    http_method_names = ['get']
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticatedCustom]

    def list(self, request, *args, **kwargs):
        data = self.serializer_class(request.user).data
        return Response(data)


class UserActivitiesView(ModelViewSet):
    """ Представление для отображения активности (действий) пользователей """

    http_method_names = ['get']
    serializer_class = UserActivitiesSerializer
    queryset = UserActivities.objects.all()
    permission_classes = [IsAuthenticatedCustom]


class UsersListView(ModelViewSet):
    """ Представление для получения списка пользователей, кроме суперпользователя """

    http_method_names = ['get']
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticatedCustom]

    def list(self, request, *args, **kwargs):
        users = self.queryset.filter(is_superuser=False)
        data = self.serializer_class(users, many=True).data
        return Response(data)
