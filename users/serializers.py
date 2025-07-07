from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.password_validation import validate_password

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfile model (address, phone, etc.).
    """
    class Meta:
        model = UserProfile
        fields = ['address', 'phone']

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the built-in User model, including nested profile.
    """
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Validates password and creates User + UserProfile.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])  # Main password
    password2 = serializers.CharField(write_only=True, required=True)  # Password confirmation

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        UserProfile.objects.create(user=user)
        return user 