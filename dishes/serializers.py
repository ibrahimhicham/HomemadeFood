from rest_framework import serializers
from .models import Category, Dish, DishReview, DishImage, DishVarietySection, DishVarietyOption
from authentication.models import User, Chef
from authentication.serializers import UserSerializer
from django.db import transaction
from django.conf import settings


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    dish_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'dish_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_dish_count(self, obj):
        """Get the number of dishes in this category"""
        return obj.dishes.count()


from rest_framework import serializers
from django.conf import settings
from .models import DishImage


class DishImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DishImage
        fields = [
            'id',
            'image',          # required for upload
            'image_url',      # returned to frontend
            'is_primary',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return settings.DEFAULT_DISH_IMAGE

    # ✅ Ensure only one primary image per dish
    def create(self, validated_data):
        dish = validated_data['dish']

        if validated_data.get('is_primary', False):
            DishImage.objects.filter(dish=dish, is_primary=True).update(is_primary=False)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Handle primary image switch
        if validated_data.get('is_primary', False):
            DishImage.objects.filter(dish=instance.dish, is_primary=True).exclude(id=instance.id).update(is_primary=False)

        return super().update(instance, validated_data)


class DishReviewSerializer(serializers.ModelSerializer):
    """Serializer for DishReview model - full version with all fields"""
    customer = UserSerializer(read_only=True)

    class Meta:
        model = DishReview
        fields = ['id', 'dish', 'customer', 'rating', 'review_text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'customer', 'created_at', 'updated_at']


class DishReviewPreviewSerializer(serializers.ModelSerializer):
    """Lightweight review serializer for dish detail preview"""
    user_name = serializers.CharField(source='customer.first_name', read_only=True)
    
    class Meta:
        model = DishReview
        fields = ['id', 'user_name', 'rating', 'review_text', 'created_at']
        read_only_fields = ['id', 'created_at']


class DishListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing dishes"""
    chef = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'price', 'is_available',
            'preparation_time', 'chef', 'category', 
            'created_at', 'average_rating', 'image'
        ]
        read_only_fields = ['id', 'created_at']

    def get_chef(self, obj):
        chef_data = {
            'id': obj.chef.id,
            'first_name': obj.chef.first_name,
            'last_name': obj.chef.last_name
        }
        # Add is_online status if chef profile exists
        if hasattr(obj.chef, 'chef'):
            chef_profile = obj.chef.chef
            if chef_profile:
                chef_data['is_online'] = chef_profile.is_online
            else:
                chef_data['is_online'] = False
        else:
            chef_data['is_online'] = False
        return chef_data

    def get_category(self, obj):
        return {
            'id': obj.category.id,
            'name': obj.category.name
        }

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

    def get_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            return primary_image.image.url
        return settings.DEFAULT_DISH_IMAGE


class DishVarietyOptionSerializer(serializers.ModelSerializer):
    """Serializer for DishVarietyOption model"""
    class Meta:
        model = DishVarietyOption
        fields = ['id', 'name', 'price_adjustment', 'is_available']


class DishVarietySectionSerializer(serializers.ModelSerializer):
    """Serializer for DishVarietySection model"""
    options = DishVarietyOptionSerializer(many=True)

    class Meta:
        model = DishVarietySection
        fields = ['id', 'name', 'description', 'is_required', 'options']


class ChefInfoSerializer(serializers.ModelSerializer):
    """Lightweight chef info serializer for dish detail response"""
    name = serializers.SerializerMethodField()
    specialties = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'rating', 'total_reviews', 'specialties', 'profile_picture', 'is_online']
        read_only_fields = ['id']

    def get_name(self, obj):
        return f"Chef {obj.first_name} {obj.last_name}"

    def get_specialties(self, obj):
        """Get chef's cuisine specialties as a list"""
        if hasattr(obj, 'chef'):
            chef_profile = obj.chef
            if chef_profile and chef_profile.cuisine_specialties:
                return [s.strip() for s in chef_profile.cuisine_specialties.split(',')]
        return []

    def get_rating(self, obj):
        """Get chef's rating from profile"""
        if hasattr(obj, 'chef'):
            chef_profile = obj.chef
            if chef_profile:
                return chef_profile.rating
        return None

    def get_total_reviews(self, obj):
        """Get chef's total review count from profile"""
        if hasattr(obj, 'chef'):
            chef_profile = obj.chef
            if chef_profile:
                return chef_profile.total_reviews
        return 0

    def get_is_online(self, obj):
        """Get chef's online status from profile"""
        if hasattr(obj, 'chef'):
            chef_profile = obj.chef
            if chef_profile:
                return chef_profile.is_online
        return False
    
    def get_profile_picture(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return settings.DEFAULT_PROFILE_PICTURE


class DishSerializer(serializers.ModelSerializer):
    """Serializer for Dish model - Full detail view"""
    chef = ChefInfoSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    images = DishImageSerializer(many=True, read_only=True)
    reviews_preview = serializers.SerializerMethodField()
    variety_sections = DishVarietySectionSerializer(many=True, required=False)
    rating_avg = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [
            'id', 'chef', 'name', 'description', 'price', 'is_available',
            'preparation_time', 'category', 'category_id', 'images',
            'reviews_preview', 'variety_sections', 'created_at', 'updated_at',
            'rating_avg', 'reviews_count'
        ]
        read_only_fields = ['id', 'chef', 'created_at', 'updated_at']

    def get_rating_avg(self, obj):
        """Calculate average rating for the dish"""
        if hasattr(obj, 'rating_avg') and obj.rating_avg is not None:
            return round(float(obj.rating_avg), 2)
        return 0.0

    def get_reviews_count(self, obj):
        """Get total number of reviews"""
        if hasattr(obj, 'reviews_count') and obj.reviews_count is not None:
            return obj.reviews_count
        return 0

    def get_reviews_preview(self, obj):
        """Get latest 3 reviews as preview"""
        if hasattr(obj, 'latest_reviews'):
            reviews = obj.latest_reviews
        else:
            reviews = obj.reviews.select_related('customer').order_by('-created_at')[:3]
        return DishReviewPreviewSerializer(reviews, many=True).data

    def create(self, validated_data):
        """Create a new dish with the authenticated chef"""
        request = self.context.get('request')
        name = validated_data.get('name')
        sections_data = validated_data.pop('variety_sections', [])
        if request and hasattr(request, 'user'):
            validated_data['chef'] = request.user

        if Dish.objects.filter(chef=validated_data['chef'], name=name).exists():
            raise serializers.ValidationError({
                "name": "You already have a dish with this name."
            })    
        dish = Dish.objects.create(**validated_data)

    # ✅ create sections + options
        for section_data in sections_data:
            options_data = section_data.pop('options', [])

            section = DishVarietySection.objects.create(
                dish=dish,
                **section_data
            )

            for option_data in options_data:
                DishVarietyOption.objects.create(
                    section=section,
                    **option_data
                )

        return dish
    @transaction.atomic
    def update(self, instance, validated_data):
        sections_data = validated_data.pop('variety_sections', None)

        # 🔴 handle name uniqueness on update
        name = validated_data.get('name', instance.name)
        chef = self.context['request'].user

        if Dish.objects.filter(
            chef=chef,
            name__iexact=name
        ).exclude(id=instance.id).exists():
            raise serializers.ValidationError({
                "name": "You already have a dish with this name."
            })

        # ✅ update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # delete old
        instance.variety_sections.all().delete()

        # ✅ update nested (ONLY if provided in PATCH)
        if sections_data is not None:

            # recreate
            for section_data in sections_data:
                options_data = section_data.pop('options', [])

                section = DishVarietySection.objects.create(
                    dish=instance,
                    **section_data
                )

                for option_data in options_data:
                    DishVarietyOption.objects.create(
                        section=section,
                        **option_data
                    )

        return instance

# Homepage Serializers

class CategoryHomeSerializer(serializers.ModelSerializer):
    """Lightweight category serializer for homepage"""

    class Meta:
        model = Category
        fields = ['id', 'name']


class FeaturedDishSerializer(DishListSerializer):
    """Extended dish serializer for homepage featured dishes"""
    # Inherits image from DishListSerializer
    description = serializers.SerializerMethodField()
    chef = serializers.SerializerMethodField()

    class Meta(DishListSerializer.Meta):
        fields = DishListSerializer.Meta.fields + ['description', 'chef']

    def get_description(self, obj):
        return obj.description

    def get_chef(self, obj):
        return {
            'id': obj.chef.id,
            'first_name': obj.chef.first_name,
            'last_name': obj.chef.last_name,
            'profile_picture': obj.chef.profile_picture.url if obj.chef.profile_picture else settings.DEFAULT_PROFILE_PICTURE
        }


class TopChefSerializer(serializers.ModelSerializer):
    """Chef serializer for homepage"""
    user = serializers.SerializerMethodField()

    class Meta:
        model = Chef
        fields = ['id', 'user', 'rating', 'total_reviews', 'cuisine_specialties']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'profile_picture': obj.user.profile_picture.url if obj.user.profile_picture else settings.DEFAULT_PROFILE_PICTURE
        }


class NewDishSerializer(serializers.ModelSerializer):
    """Lightweight dish serializer for new dishes"""
    chef_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = ['id', 'name', 'price', 'chef_name', 'image', 'created_at']

    def get_chef_name(self, obj):
        return f"{obj.chef.first_name} {obj.chef.last_name}"

    def get_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            return primary_image.image.url
        return settings.DEFAULT_DISH_IMAGE


class HomePageSerializer(serializers.Serializer):
    """Aggregated homepage response"""
    categories = CategoryHomeSerializer(many=True)
    featured_dishes = FeaturedDishSerializer(many=True)
    top_chefs = TopChefSerializer(many=True)
    new_dishes = NewDishSerializer(many=True)