from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'user_type', 'phone', 'bio', 'date_of_birth', 'country', 'city',
            'company', 'job_title', 'experience_years', 'skill_level',
            'linkedin_url', 'github_url', 'portfolio_url'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone', 'bio', 'profile_picture', 'date_of_birth',
            'country', 'city', 'address', 'company', 'job_title', 'experience_years',
            'skill_level', 'linkedin_url', 'github_url', 'portfolio_url',
            'points', 'is_verified', 'is_active_developer', 'subscription_tier',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'email', 'username', 'points', 'is_verified', 
            'is_active_developer', 'subscription_tier', 'created_at', 'updated_at'
        )


class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'email', 'user_type', 
            'is_verified', 'is_active_developer', 'created_at'
        )


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom user data to the response
        data['user'] = UserProfileSerializer(self.user).data
        
        return data
