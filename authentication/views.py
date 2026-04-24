from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.contrib.auth import authenticate, get_user_model
from rest_framework.authtoken.models import Token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .serializers import (
    SignupSerializer, LoginSerializer, UserSerializer, PaymentCardSerializer,
    ChefSerializer, ConsumerSerializer
)
from .models import PaymentCard, Chef, Consumer
from .permissions import UserProfilePermission
import cloudinary.uploader


# Import pagination from dishes app
from dishes.pagination import StandardResultsSetPagination
from rest_framework.parsers import MultiPartParser, FormParser

User = get_user_model()


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user_type = request.data.get('user_type')
        
        # Return appropriate serializer based on user type
        if user_type == 'chef':
            chef = Chef.objects.get(user=user)
            data = ChefSerializer(chef).data
        else:
            consumer = Consumer.objects.get(user=user)
            data = ConsumerSerializer(consumer).data
        
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        
        # Return user type specific data
        user_type = user.get_user_type()
        user_data = UserSerializer(user).data
        
        response_data = {
            'token': token.key,
            'user': user_data,
        }
        
        if user_type == 'chef':
            chef = Chef.objects.get(user=user)
            response_data['profile'] = ChefSerializer(chef).data
        elif user_type == 'consumer':
            consumer = Consumer.objects.get(user=user)
            response_data['profile'] = ConsumerSerializer(consumer).data
        
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # delete token for the user
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Logged out'}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify the authenticated user matches the provided email
        if request.user.email != email:
            return Response(
                {'detail': 'Email does not match authenticated user'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        uid = urlsafe_base64_encode(force_bytes(request.user.pk))
        token = default_token_generator.make_token(request.user)
        # For development we return token in response. In production, email this link.
        return Response({'uid': uid, 'token': token}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        if not all([uid, token, new_password]):
            return Response({'detail': 'uid, token and new_password are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            uid_int = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_int)
        except Exception:
            return Response({'detail': 'Invalid uid'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password has been reset'}, status=status.HTTP_200_OK)


class PaymentCardCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentCardSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        card = serializer.save()
        return Response({'card': serializer.data}, status=status.HTTP_201_CREATED)


class UserProfileView(APIView):
    """
    View to retrieve user profiles with access controls:
    - Consumer can read chef profiles
    - User can read their own profile
    - Chef can update their own profile
    - Consumer can update their own profile
    """
    permission_classes = [permissions.IsAuthenticated, UserProfilePermission]

    def get(self, request, user_id):
        # Get the user whose profile is being requested
        target_user = get_object_or_404(User, id=user_id)

        # Check the permission using the custom permission class
        if not self.permission_classes[1]().has_object_permission(request, self, target_user):
            return Response(
                {'detail': 'You do not have permission to view this profile'},
                status=status.HTTP_403_FORBIDDEN
            )

        # User can view their own profile or consumer can view chef profile
        user_type = target_user.get_user_type()
        if user_type == 'chef':
            chef = Chef.objects.get(user=target_user)
            serializer = ChefSerializer(chef)
        elif user_type == 'consumer':
            consumer = Consumer.objects.get(user=target_user)
            serializer = ConsumerSerializer(consumer)
        else:
            serializer = UserSerializer(target_user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, user_id):
        # Only allow user to update their own profile
        target_user = get_object_or_404(User, id=user_id)

        if request.user.id != target_user.id:
            return Response(
                {'detail': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if the user is a chef
        if hasattr(request.user, 'chef'):
            chef = get_object_or_404(Chef, user=target_user)
            serializer = ChefSerializer(chef, data=request.data, partial=False)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is a consumer
        elif hasattr(request.user, 'consumer'):
            consumer = get_object_or_404(Consumer, user=target_user)
            serializer = ConsumerSerializer(consumer, data=request.data, partial=False)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If user is neither chef nor consumer, return error
        return Response(
            {'detail': 'User profile type not recognized'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, user_id):
        # Only allow user to update their own profile
        target_user = get_object_or_404(User, id=user_id)

        if request.user.id != target_user.id:
            return Response(
                {'detail': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if the user is a chef
        if hasattr(request.user, 'chef'):
            chef = get_object_or_404(Chef, user=target_user)
            serializer = ChefSerializer(chef, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is a consumer
        elif hasattr(request.user, 'consumer'):
            consumer = get_object_or_404(Consumer, user=target_user)
            serializer = ConsumerSerializer(consumer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If user is neither chef nor consumer, return error
        return Response(
            {'detail': 'User profile type not recognized'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ProfilePictureUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        file = request.FILES.get('profile_picture')
        if not file:
            return Response(
                {'detail': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if user.profile_picture:
            cloudinary.uploader.destroy(user.profile_picture.public_id)  # Delete old image from Cloudinary

        # Upload new image
        user.profile_picture = file
        user.save()

        return Response(
            UserSerializer(user, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

class ChefToggleOnlineView(APIView):
    """Toggle chef's online status (available to accept orders)"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if the authenticated user is a chef
        if not hasattr(request.user, 'chef'):
            return Response(
                {'detail': 'Only chefs can toggle online status'},
                status=status.HTTP_403_FORBIDDEN
            )

        chef = request.user.chef
        chef.is_online = not chef.is_online
        chef.save()

        serializer = ChefSerializer(chef)
        return Response({
            'detail': f'Chef is now {"online" if chef.is_online else "offline"}',
            'is_online': chef.is_online,
            'chef': serializer.data
        }, status=status.HTTP_200_OK)


class ChefListView(generics.ListAPIView):
    """
    List all chefs with optional filtering:
    - ?search={query}: Search by chef name or bio
    - ?is_online=true/false: Filter by online status
    - ?is_verified=true/false: Filter by verification status
    - ?min_rating={rating}: Filter by minimum rating
    """
    serializer_class = ChefSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Chef.objects.select_related('user').all()

        # Search functionality - search by chef name or bio
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(bio__icontains=search_query) |
                Q(cuisine_specialties__icontains=search_query)
            )

        # Filter by online status
        is_online = self.request.query_params.get('is_online', None)
        if is_online is not None:
            is_online = is_online.lower() == 'true'
            queryset = queryset.filter(is_online=is_online)

        # Filter by verification status
        is_verified = self.request.query_params.get('is_verified', None)
        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'
            queryset = queryset.filter(is_verified=is_verified)

        # Filter by minimum rating
        min_rating = self.request.query_params.get('min_rating', None)
        if min_rating is not None:
            queryset = queryset.filter(rating__gte=min_rating)

        return queryset
