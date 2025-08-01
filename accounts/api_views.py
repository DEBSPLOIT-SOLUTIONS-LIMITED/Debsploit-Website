from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, UserListSerializer,
    PasswordChangeSerializer, CustomTokenObtainPairSerializer
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user_type', 'is_verified', 'is_active_developer', 'subscription_tier']
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['created_at', 'last_login', 'first_name', 'last_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserProfileSerializer

    def get_permissions(self):
        if self.action == 'create':
            # Allow anyone to register
            return [permissions.AllowAny()]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            # Users can only view/edit their own profile unless they're staff
            return [permissions.IsAuthenticated()]
        else:
            # Admin actions require staff permissions
            return [permissions.IsAdminUser()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        elif user.is_authenticated:
            # Non-staff users can only see their own profile
            return User.objects.filter(id=user.id)
        return User.objects.none()

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get or update current user's profile"""
        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)
        
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Change user password"""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def verify_user(self, request, pk=None):
        """Verify a user (admin only)"""
        user = self.get_object()
        user.is_verified = True
        user.save()
        return Response({'message': f'User {user.email} has been verified'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def unverify_user(self, request, pk=None):
        """Unverify a user (admin only)"""
        user = self.get_object()
        user.is_verified = False
        user.save()
        return Response({'message': f'User {user.email} has been unverified'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def deactivate(self, request, pk=None):
        """Deactivate a user account (admin only)"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': f'User {user.email} has been deactivated'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def activate(self, request, pk=None):
        """Activate a user account (admin only)"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': f'User {user.email} has been activated'})
