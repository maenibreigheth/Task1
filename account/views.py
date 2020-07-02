from django.shortcuts import get_object_or_404
from rest_framework import authentication, permissions, mixins
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from .serializers import UserSerializer, AuthTokenSerializer, PasswordChangeSerializer, CreateUserSerializer, \
    UpdateUserSerializer
from .models import User
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from rest_framework.views import APIView


class UserRelatedView(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      GenericViewSet):
    """
    A view for the superusers and authenticated users to retrieve ('GET') or update ('PUT', 'PATCH') or soft delete (
    'DELETE') the users data through the users/ url for superusers, and 'users/me/' url for the authenticated users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'

    def update(self, request, pk=None):
        user = get_object_or_404(self.queryset, pk=pk)
        serializer = UpdateUserSerializer(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user, validated_data=serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        user = get_object_or_404(self.queryset, pk=pk)
        serializer = UpdateUserSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user, validated_data=serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        user = get_object_or_404(self.queryset, pk=pk)
        user.is_active = False
        user.save()
        return Response('Object deactivated successfully', status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def create_user(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create(validated_data=request.data)
        user.save()
        # user = serializer.create(validated_data=serializer.validated_data)
        token = default_token_generator.make_token(user)
        mail_subject = 'Activate your account.'

        message = 'link: ' + 'http://127.0.0.1:8000/activate/{}/{}'.format(user.id, token)
        to_email = serializer.data['email']
        email = EmailMessage(
            mail_subject, message, to=[to_email]
        )
        email.send()
        # serializer.data['detail'] = "Please confirm your email address to complete the registration"
        return Response('Please confirm your email address to complete the registration', status=status.HTTP_201_CREATED)

    # @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    # def activate(self, request, pk, token):
    #     try:
    #         user = User.objects.get(pk=pk)
    #     except(TypeError, ValueError, OverflowError, User.DoesNotExist):
    #         user = None
    #     if user is not None and default_token_generator.check_token(user, token):
    #         user.is_active = True
    #         user.save()
    #         return Response('Thank you for your email confirmation. Now you can login your account.')
    #     else:
    #         return Response('Activation link is invalid!')

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id})

    @action(detail=False, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.validated_data['user']
        instance.set_password(serializer.data.get('new_password'))
        instance.save()

        return Response('Password changed successfully')

    # url_path for customizing all the methods
    @action(detail=False, methods=['get', 'put', 'patch', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):

        user = request.user

        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'PUT':
            serializer = UpdateUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=user, validated_data=serializer.validated_data)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        if request.method == 'PATCH':
            serializer = UpdateUserSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=user, validated_data=serializer.validated_data)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        if request.method == 'DELETE':
            user.is_active = False
            user.save()
            return Response("User is deactivated", status=status.HTTP_204_NO_CONTENT)


class ActivateUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk, token):

        user = get_object_or_404(User, id=pk)

        if user.is_active:
            return Response('already activated', status=status.HTTP_208_ALREADY_REPORTED)

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response('Thank you for your email confirmation. Now you can login your account.',
                            status=status.HTTP_202_ACCEPTED)
        else:
            return Response('Activation link is invalid!', status=status.HTTP_400_BAD_REQUEST)
