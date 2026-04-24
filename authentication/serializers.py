from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PaymentCard, Chef, Consumer
from django.conf import settings


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'profile_picture', 'address_longitude', 'address_latitude',
            'created_at', 'updated_at', 'is_active', 'user_type'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_type(self, obj):
        return obj.get_user_type()


class ChefSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Chef
        fields = [
            'id', 'user', 'rating', 'total_reviews', 'bio',
            'cuisine_specialties', 'years_of_experience', 'is_verified',
            'is_online', 'created_at', 'updated_at'
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        return super().update(instance, validated_data)


class ConsumerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Consumer
        fields = [
            'id', 'user',
            'total_orders', 'created_at', 'updated_at'
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        return super().update(instance, validated_data)


class SignupSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)
    address_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    address_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    user_type = serializers.ChoiceField(choices=['chef', 'consumer'])
    # Optional chef fields
    bio = serializers.CharField(required=False, allow_blank=True)
    cuisine_specialties = serializers.CharField(required=False, allow_blank=True)
    years_of_experience = serializers.IntegerField(required=False, default=0)


    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already in use')
        return value

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('Phone number already in use')
        return value

    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        # Pop chef/consumer fields
        bio = validated_data.pop('bio', '')
        cuisine_specialties = validated_data.pop('cuisine_specialties', '')
        years_of_experience = validated_data.pop('years_of_experience', 0)


        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Create Chef or Consumer profile
        if user_type == 'chef':
            Chef.objects.create(
                user=user,
                bio=bio,
                cuisine_specialties=cuisine_specialties,
                years_of_experience=years_of_experience
            )
        else:  # consumer
            Consumer.objects.create(
                user=user,
            )

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PaymentCardSerializer(serializers.ModelSerializer):
    card_number = serializers.CharField(write_only=True, min_length=12, max_length=19)

    class Meta:
        model = PaymentCard
        fields = ['id', 'card_number', 'cardholder_name', 'exp_month', 'exp_year', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        card_number = validated_data.pop('card_number')
        last4 = card_number[-4:]
        validated_data['card_last4'] = last4
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
