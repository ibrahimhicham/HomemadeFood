from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Dish, DishReview, DishImage
from authentication.models import Chef, Consumer

User = get_user_model()


class DishesModelTestCase(TestCase):
    """Test cases for dishes models"""

    def setUp(self):
        # Create a chef user
        self.chef = User.objects.create_user(
            email='chef@example.com',
            first_name='Chef',
            last_name='Test',
            phone_number='1234567890',
            password='testpassword123'
        )
        
        # Create a customer user
        self.customer = User.objects.create_user(
            email='customer@example.com',
            first_name='Customer',
            last_name='Test',
            phone_number='0987654321',
            password='testpassword123'
        )

    def test_category_creation(self):
        """Test creating a category"""
        category = Category.objects.create(
            name='Main Course',
            description='Delicious main courses'
        )
        
        self.assertEqual(category.name, 'Main Course')
        self.assertEqual(category.description, 'Delicious main courses')
        self.assertIsNotNone(category.created_at)

    def test_dish_creation(self):
        """Test creating a dish"""
        category = Category.objects.create(name='Appetizers')
        
        dish = Dish.objects.create(
            chef=self.chef,
            name='Test Dish',
            description='A delicious test dish',
            category=category,
            price=Decimal('15.99'),
            preparation_time=30
        )
        
        self.assertEqual(dish.name, 'Test Dish')
        self.assertEqual(dish.chef, self.chef)
        self.assertEqual(dish.category, category)
        self.assertEqual(dish.price, Decimal('15.99'))
        self.assertTrue(dish.is_available)

    def test_dish_review_creation(self):
        """Test creating a dish review"""
        category = Category.objects.create(name='Main Course')
        
        dish = Dish.objects.create(
            chef=self.chef,
            name='Test Dish',
            description='A delicious test dish',
            category=category,
            price=Decimal('15.99'),
            preparation_time=30
        )
        
        review = DishReview.objects.create(
            dish=dish,
            customer=self.customer,
            rating=5,
            review_text='Excellent dish!'
        )
        
        self.assertEqual(review.dish, dish)
        self.assertEqual(review.customer, self.customer)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.review_text, 'Excellent dish!')

    def test_dish_image_creation(self):
        """Test creating a dish image"""
        category = Category.objects.create(name='Main Course')
        
        dish = Dish.objects.create(
            chef=self.chef,
            name='Test Dish',
            description='A delicious test dish',
            category=category,
            price=Decimal('15.99'),
            preparation_time=30
        )
        
        image = DishImage.objects.create(
            dish=dish,
            image_url='https://example.com/image.jpg',
            is_primary=True
        )
        
        self.assertEqual(image.dish, dish)
        self.assertEqual(image.image_url, 'https://example.com/image.jpg')
        self.assertTrue(image.is_primary)


class DishesAPITestCase(APITestCase):
    """Test cases for dishes API endpoints"""

    def setUp(self):
        # Create users
        self.chef = User.objects.create_user(
            email='chef@example.com',
            first_name='Chef',
            last_name='Test',
            phone_number='1234567890',
            password='testpassword123'
        )
        
        self.customer = User.objects.create_user(
            email='customer@example.com',
            first_name='Customer',
            last_name='Test',
            phone_number='0987654321',
            password='testpassword123'
        )
        
        # Create a category and dish
        self.category = Category.objects.create(
            name='Main Course',
            description='Delicious main courses'
        )
        
        self.dish = Dish.objects.create(
            chef=self.chef,
            name='Test Dish',
            description='A delicious test dish',
            category=self.category,
            price=Decimal('15.99'),
            preparation_time=30
        )

    def test_get_categories_list(self):
        """Test getting list of categories"""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_dish_detail(self):
        """Test getting dish detail"""
        url = reverse('dish-detail', kwargs={'pk': self.dish.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Dish')

    def test_get_dishes_by_category(self):
        """Test getting dishes by category"""
        url = reverse('dishes-by-category', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_dish_reviews(self):
        """Test getting dish reviews with pagination"""
        url = reverse('dish-reviews', kwargs={'dish_id': self.dish.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response is now paginated
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])


class ChefDishCreationAPITestCase(APITestCase):
    """Test cases for chef dish creation functionality"""

    def setUp(self):
        # Create chef user with Chef profile
        self.chef = User.objects.create_user(
            email='chef.test@example.com',
            first_name='Test',
            last_name='Chef',
            phone_number='1234567890',
            password='chefpassword123'
        )
        Chef.objects.create(user=self.chef)

        # Create another chef (for permission tests)
        self.other_chef = User.objects.create_user(
            email='other.chef@example.com',
            first_name='Other',
            last_name='Chef',
            phone_number='0987654321',
            password='chefpassword456'
        )
        Chef.objects.create(user=self.other_chef)

        # Create consumer user with Consumer profile
        self.consumer = User.objects.create_user(
            email='consumer@example.com',
            first_name='Test',
            last_name='Consumer',
            phone_number='1122334455',
            password='consumerpassword123'
        )
        Consumer.objects.create(user=self.consumer)

        # Create category
        self.category = Category.objects.create(
            name='Italian',
            description='Delicious Italian cuisine'
        )

        # Login URLs
        self.login_url = reverse('login')

    def login_user(self, email, password):
        """Helper method to login and set auth token"""
        response = self.client.post(self.login_url, {
            'email': email,
            'password': password
        })
        if response.status_code == status.HTTP_200_OK:
            token = response.data.get('token')
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        return response

    def test_chef_can_create_dish(self):
        """Test that a chef can successfully create a dish"""
        # Login as chef
        login_response = self.login_user('chef.test@example.com', 'chefpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Create dish
        url = reverse('chef-dish-list')
        dish_data = {
            'name': 'Margherita Pizza',
            'description': 'Classic Italian pizza with tomato sauce, mozzarella, and basil',
            'category_id': self.category.id,
            'price': '12.99',
            'preparation_time': 25,
            'is_available': True
        }

        response = self.client.post(url, dish_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Margherita Pizza')
        self.assertEqual(response.data['chef']['name'], 'Chef Test Chef')
        self.assertEqual(response.data['category']['name'], 'Italian')
        self.assertEqual(float(response.data['price']), 12.99)
        self.assertEqual(response.data['preparation_time'], 25)
        self.assertTrue(response.data['is_available'])

        # Verify dish exists in database
        dish = Dish.objects.get(name='Margherita Pizza')
        self.assertEqual(dish.chef, self.chef)
        self.assertEqual(dish.category, self.category)

    def test_consumer_cannot_create_dish(self):
        """Test that a consumer cannot create dishes"""
        # Login as consumer
        login_response = self.login_user('consumer@example.com', 'consumerpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Try to create dish
        url = reverse('chef-dish-list')
        dish_data = {
            'name': 'Test Dish',
            'description': 'Test description',
            'category_id': self.category.id,
            'price': '10.99',
            'preparation_time': 20
        }

        response = self.client.post(url, dish_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_create_dish(self):
        """Test that unauthenticated users cannot create dishes"""
        url = reverse('chef-dish-list')
        dish_data = {
            'name': 'Test Dish',
            'description': 'Test description',
            'category_id': self.category.id,
            'price': '10.99',
            'preparation_time': 20
        }

        response = self.client.post(url, dish_data, format='json')

        # Should be redirected or return 401/403
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_chef_cannot_create_duplicate_dish(self):
        """Test that a chef cannot create dishes with duplicate names"""
        # Login as chef
        login_response = self.login_user('chef.test@example.com', 'chefpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Create first dish
        url = reverse('chef-dish-list')
        dish_data = {
            'name': 'Pasta Carbonara',
            'description': 'Traditional Italian pasta',
            'category_id': self.category.id,
            'price': '14.99',
            'preparation_time': 30
        }

        response1 = self.client.post(url, dish_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Try to create dish with same name - should fail due to unique constraint
        from django.db.utils import IntegrityError
        with self.assertRaises(IntegrityError):
            self.client.post(url, dish_data, format='json')

    def test_chef_cannot_create_dish_with_invalid_category(self):
        """Test that dish creation fails with invalid category"""
        # Login as chef
        login_response = self.login_user('chef.test@example.com', 'chefpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        url = reverse('chef-dish-list')
        dish_data = {
            'name': 'Test Dish',
            'description': 'Test description',
            'category_id': 99999,  # Non-existent category
            'price': '10.99',
            'preparation_time': 20
        }

        response = self.client.post(url, dish_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chef_cannot_create_dish_without_required_fields(self):
        """Test that dish creation fails without required fields"""
        # Login as chef
        login_response = self.login_user('chef.test@example.com', 'chefpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        url = reverse('chef-dish-list')

        # Missing name
        dish_data = {
            'description': 'Test description',
            'category_id': self.category.id,
            'price': '10.99',
            'preparation_time': 20
        }

        response = self.client.post(url, dish_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

        # Missing price
        dish_data = {
            'name': 'Test Dish',
            'description': 'Test description',
            'category_id': self.category.id,
            'preparation_time': 20
        }

        response = self.client.post(url, dish_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)

    def test_chef_can_list_own_dishes(self):
        """Test that a chef can list their own dishes"""
        # Login as chef
        login_response = self.login_user('chef.test@example.com', 'chefpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Create some dishes
        Dish.objects.create(
            chef=self.chef,
            name='Dish 1',
            description='Description 1',
            category=self.category,
            price=Decimal('10.99'),
            preparation_time=20
        )

        Dish.objects.create(
            chef=self.chef,
            name='Dish 2',
            description='Description 2',
            category=self.category,
            price=Decimal('15.99'),
            preparation_time=25
        )

        # Create dish for other chef (should not appear)
        Dish.objects.create(
            chef=self.other_chef,
            name='Other Dish',
            description='Other description',
            category=self.category,
            price=Decimal('12.99'),
            preparation_time=22
        )

        url = reverse('chef-dish-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        dish_names = [dish['name'] for dish in response.data]
        self.assertIn('Dish 1', dish_names)
        self.assertIn('Dish 2', dish_names)
        self.assertNotIn('Other Dish', dish_names)

    def test_chef_can_update_own_dish(self):
        """Test that a chef can update their own dish"""
        # Login as chef
        login_response = self.login_user('chef.test@example.com', 'chefpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Create a dish
        dish = Dish.objects.create(
            chef=self.chef,
            name='Original Dish',
            description='Original description',
            category=self.category,
            price=Decimal('10.99'),
            preparation_time=20
        )

        # Update the dish
        url = reverse('chef-dish-detail', kwargs={'pk': dish.pk})
        update_data = {
            'name': 'Updated Dish',
            'description': 'Updated description',
            'category_id': self.category.id,
            'price': '15.99',
            'preparation_time': 30,
            'is_available': False
        }

        response = self.client.patch(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Dish')
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertEqual(float(response.data['price']), 15.99)
        self.assertFalse(response.data['is_available'])

    def test_chef_cannot_update_other_chef_dish(self):
        """Test that a chef cannot update another chef's dish"""
        # Login as chef
        login_response = self.login_user('chef.test@example.com', 'chefpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Create dish for other chef
        dish = Dish.objects.create(
            chef=self.other_chef,
            name='Other Chef Dish',
            description='Original description',
            category=self.category,
            price=Decimal('10.99'),
            preparation_time=20
        )

        # Try to update
        url = reverse('chef-dish-detail', kwargs={'pk': dish.pk})
        update_data = {
            'name': 'Hacked Dish',
        }

        response = self.client.patch(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_chef_can_delete_own_dish(self):
        """Test that a chef can delete their own dish"""
        # Login as chef
        login_response = self.login_user('chef.test@example.com', 'chefpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Create a dish
        dish = Dish.objects.create(
            chef=self.chef,
            name='Dish to Delete',
            description='Will be deleted',
            category=self.category,
            price=Decimal('10.99'),
            preparation_time=20
        )

        # Delete the dish
        url = reverse('chef-dish-detail', kwargs={'pk': dish.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify dish is deleted
        with self.assertRaises(Dish.DoesNotExist):
            Dish.objects.get(pk=dish.pk)

    def test_chef_cannot_delete_other_chef_dish(self):
        """Test that a chef cannot delete another chef's dish"""
        # Login as chef
        login_response = self.login_user('chef.test@example.com', 'chefpassword123')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Create dish for other chef
        dish = Dish.objects.create(
            chef=self.other_chef,
            name='Other Chef Dish',
            description='Description',
            category=self.category,
            price=Decimal('10.99'),
            preparation_time=20
        )

        # Try to delete
        url = reverse('chef-dish-detail', kwargs={'pk': dish.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify dish still exists
        dish.refresh_from_db()
        self.assertIsNotNone(dish)