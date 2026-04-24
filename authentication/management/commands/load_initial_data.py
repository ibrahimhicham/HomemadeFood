"""
Management command to load initial data for the Homemade Food application
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from authentication.models import User, Chef, Consumer
from dishes.models import Category, Dish, DishImage, DishReview, DishVarietySection, DishVarietyOption


class Command(BaseCommand):
    help = 'Load initial data for testing'

    def handle(self, *args, **options):
        # Create users with proper passwords
        chef_john = User.objects.create(
            email="chef.john@example.com",
            first_name="John",
            last_name="Chef",
            phone_number="+1234567890",
            address_longitude=-122.4194,
            address_latitude=37.7749,
            is_active=True,
            is_staff=False,
            password=make_password("chef123")
        )

        chef_maria = User.objects.create(
            email="chef.maria@example.com",
            first_name="Maria",
            last_name="Gonzalez",
            phone_number="+1987654321",
            address_longitude=-122.3301,
            address_latitude=37.6879,
            is_active=True,
            is_staff=False,
            password=make_password("chef456")
        )

        consumer_sarah = User.objects.create(
            email="consumer.sarah@example.com",
            first_name="Sarah",
            last_name="Johnson",
            phone_number="+1555123456",
            address_longitude=-122.2711,
            address_latitude=37.8044,
            is_active=True,
            is_staff=False,
            password=make_password("consumer123")
        )

        consumer_mike = User.objects.create(
            email="consumer.mike@example.com",
            first_name="Mike",
            last_name="Davis",
            phone_number="+1555987654",
            address_longitude=-122.4473,
            address_latitude=37.7622,
            is_active=True,
            is_staff=False,
            password=make_password("consumer456")
        )

        # Create chef profiles
        Chef.objects.create(
            user=chef_john,
            rating=4.8,
            total_reviews=120,
            bio="Experienced Italian chef with 10 years in the industry.",
            cuisine_specialties="Italian, Mediterranean",
            years_of_experience=10,
            is_verified=True
        )

        Chef.objects.create(
            user=chef_maria,
            rating=4.6,
            total_reviews=85,
            bio="Award-winning Mexican chef specializing in authentic recipes.",
            cuisine_specialties="Mexican, Tex-Mex",
            years_of_experience=8,
            is_verified=True
        )

        # Create consumer profiles
        Consumer.objects.create(
            user=consumer_sarah,
            total_orders=25
        )

        Consumer.objects.create(
            user=consumer_mike,
            total_orders=18
        )

        # Create payment cards
        from authentication.models import PaymentCard
        PaymentCard.objects.create(
            user=consumer_sarah,
            card_last4="1111",
            cardholder_name="Sarah Johnson",
            exp_month=12,
            exp_year=2027,
            is_default=True
        )

        PaymentCard.objects.create(
            user=consumer_mike,
            card_last4="2222",
            cardholder_name="Mike Davis",
            exp_month=6,
            exp_year=2026,
            is_default=True
        )

        # Create categories
        italian_category = Category.objects.create(
            name="Italian",
            description="Authentic Italian cuisine"
        )

        mexican_category = Category.objects.create(
            name="Mexican",
            description="Traditional Mexican dishes"
        )

        asian_category = Category.objects.create(
            name="Asian",
            description="Fusion Asian cuisine"
        )

        american_category = Category.objects.create(
            name="American",
            description="Classic American comfort food"
        )

        # Create dishes
        spaghetti_carbonara = Dish.objects.create(
            chef=chef_john,
            name="Spaghetti Carbonara",
            description="Classic Roman pasta with eggs, cheese, pancetta and pepper",
            category=italian_category,
            price=15.99,
            is_available=True,
            preparation_time=20
        )

        margherita_pizza = Dish.objects.create(
            chef=chef_john,
            name="Margherita Pizza",
            description="Traditional Neapolitan pizza with tomato, mozzarella and basil",
            category=italian_category,
            price=18.50,
            is_available=True,
            preparation_time=25
        )

        chicken_tacos = Dish.objects.create(
            chef=chef_maria,
            name="Chicken Tacos",
            description="Soft corn tortillas filled with seasoned chicken, cilantro and onion",
            category=mexican_category,
            price=12.99,
            is_available=True,
            preparation_time=15
        )

        beef_burrito = Dish.objects.create(
            chef=chef_maria,
            name="Beef Burrito",
            description="Large flour tortilla with seasoned beef, rice, beans, cheese and salsa",
            category=mexican_category,
            price=14.99,
            is_available=True,
            preparation_time=20
        )

        # Create dish images
        DishImage.objects.create(
            dish=spaghetti_carbonara,
            image=None,
            is_primary=True
        )

        DishImage.objects.create(
            dish=margherita_pizza,
            image=None,
            is_primary=True
        )

        DishImage.objects.create(
            dish=chicken_tacos,
            image=None,
            is_primary=True
        )

        DishImage.objects.create(
            dish=beef_burrito,
            image=None,
            is_primary=True
        )

        # Create dish reviews
        DishReview.objects.create(
            dish=spaghetti_carbonara,
            customer=consumer_sarah,
            rating=5,
            review_text="Absolutely delicious! Authentic taste, just like in Rome."
        )

        DishReview.objects.create(
            dish=spaghetti_carbonara,
            customer=consumer_mike,
            rating=4,
            review_text="Great carbonara, though I prefer it with a bit more pepper."
        )

        DishReview.objects.create(
            dish=margherita_pizza,
            customer=consumer_sarah,
            rating=5,
            review_text="Best pizza I've had outside of Italy!"
        )

        DishReview.objects.create(
            dish=chicken_tacos,
            customer=consumer_mike,
            rating=5,
            review_text="Perfectly seasoned chicken and fresh tortillas. Will order again!"
        )

        # Create dish variety sections and options
        size_options = DishVarietySection.objects.create(
            dish=spaghetti_carbonara,
            name="Size Options",
            description="Choose your preferred portion size",
            is_required=False
        )

        crust_types = DishVarietySection.objects.create(
            dish=margherita_pizza,
            name="Crust Type",
            description="Select your preferred crust",
            is_required=True
        )

        spice_levels = DishVarietySection.objects.create(
            dish=chicken_tacos,
            name="Spice Level",
            description="How spicy would you like your tacos?",
            is_required=False
        )

        # Create dish variety options
        DishVarietyOption.objects.create(
            section=size_options,
            name="Small",
            price_adjustment=0.00,
            is_available=True
        )

        DishVarietyOption.objects.create(
            section=size_options,
            name="Medium",
            price_adjustment=2.00,
            is_available=True
        )

        DishVarietyOption.objects.create(
            section=size_options,
            name="Large",
            price_adjustment=4.00,
            is_available=True
        )

        DishVarietyOption.objects.create(
            section=crust_types,
            name="Thin Crust",
            price_adjustment=0.00,
            is_available=True
        )

        DishVarietyOption.objects.create(
            section=crust_types,
            name="Thick Crust",
            price_adjustment=1.50,
            is_available=True
        )

        DishVarietyOption.objects.create(
            section=spice_levels,
            name="Mild",
            price_adjustment=0.00,
            is_available=True
        )

        DishVarietyOption.objects.create(
            section=spice_levels,
            name="Medium",
            price_adjustment=0.00,
            is_available=True
        )

        DishVarietyOption.objects.create(
            section=spice_levels,
            name="Hot",
            price_adjustment=1.00,
            is_available=True
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded initial data for testing')
        )