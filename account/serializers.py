from abc import ABC

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework import exceptions


class UserSerializer(serializers.ModelSerializer):
    # Serializer for the Account object

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'first_name', 'last_name', 'gender', 'image']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 6}}

    def update(self, instance, validated_data):
        # Update an account, setting the password correctly and return it
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    # Serializer for the Account authenticated object

    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if user is None:
            msg = _('Unable to authenticate with provided credentials')
            raise exceptions.NotAuthenticated(msg)
        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    model = get_user_model()

    old_password = serializers.CharField(max_length=128, allow_blank=False, required=True)
    new_password = serializers.CharField(max_length=128, allow_blank=False, required=True)
    confirm_password = serializers.CharField(max_length=128, allow_blank=False, required=True)

    def validate(self, attrs):
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        user = self.context.get('request').user
        if not user.check_password(old_password):
            raise serializers.ValidationError(_("Old password doesn't match"))

        if not new_password == confirm_password:
            raise serializers.ValidationError(_("Passwords doesn't match"))

        return attrs