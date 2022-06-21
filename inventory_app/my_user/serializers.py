from rest_framework import serializers

from .models import CustomUser, UserActivities, ROLES


class CreateUserSerializer(serializers.Serializer):
    """ Сериализатор для создания пользователя """

    email = serializers.EmailField()
    fullname = serializers.CharField()
    role = serializers.ChoiceField(ROLES)


class LoginSerializer(serializers.Serializer):
    """ Сериализатор для входа пользователя """

    email = serializers.EmailField()
    password = serializers.CharField(required=False)
    is_new_user = serializers.BooleanField(default=False, required=False)


class UpdatePasswordSerializer(serializers.Serializer):
    """ Сераилизатор для обновления пароля """

    user_id = serializers.CharField()
    password = serializers.CharField()


class CustomUserSerializer(serializers.ModelSerializer):
    """ Сериализатор для получения информации о пользователе """

    class Meta:
        model = CustomUser
        exclude = ('password', )


class UserActivitiesSerializer(serializers.ModelSerializer):
    """ Сериализатор активности пользователей """

    class Meta:
        model = UserActivities
        fields = '__all__'
