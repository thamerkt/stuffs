from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from .models import (
    Stuff, Category, EquipmentImage, Review, StuffManagement, test,
    Visitor, ItemView, CartActivity, Rental,
    SiteStat, TrafficSource, DeviceStat, CategoryStat,Favorite
)
from rest_framework.views import APIView
from .serializers import (
    StuffSerializer, CategorySerializer, ReviewsSerializer, EquipmentImageSerializer,
    StuffManagementSerializer, TestSerializer,
    VisitorSerializer, ItemViewSerializer, CartActivitySerializer, RentalSerializer,
    SiteStatSerializer, TrafficSourceSerializer, DeviceStatSerializer, CategoryStatSerializer,WishSerializer
)
import pika
from rest_framework.permissions import AllowAny
from django_filters import rest_framework as filters
from rest_framework.parsers import MultiPartParser, FormParser
import requests 
import json 
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import StuffManagement
from .serializers import StuffManagementSerializer

# Define a filter class for Stuff
class StuffFilter(filters.FilterSet):
    category = filters.NumberFilter(field_name='category', lookup_expr='exact')
    user = filters.NumberFilter(field_name='user', lookup_expr='exact')
    rental_zone = filters.CharFilter(field_name='stuff_management__rental_zone', lookup_expr='exact')  # Correct filtering for rental_zone

    class Meta:
        model = Stuff
        fields = ['category', 'user', 'rental_zone']

import httpx
class StuffViewSet(viewsets.ModelViewSet):
    queryset = Stuff.objects.all()
    serializer_class = StuffSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    filterset_class = StuffFilter  # DjangoFilterBackend filter class

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        user = self.request.query_params.get('user')
        rental_zone = self.request.query_params.get('rental_zone')

        if category:
            queryset = queryset.filter(category__id=category)
        if user:
            queryset = queryset.filter(user=user)
        if rental_zone:
            queryset = queryset.filter(stuff_management__rental_zone=rental_zone)

        return queryset

    @action(detail=True, methods=['post'], url_path='draft')
    def set_draft(self, request, pk=None):
        """Set the product status to 'draft'."""
        stuff = self.get_object()
        stuff.status = 'draft'
        stuff.save()
        serializer = self.get_serializer(stuff)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='publish')
    def set_published(self, request, pk=None):
        """Set the product status to 'published'."""
        stuff = self.get_object()
        stuff.status = 'published'
        stuff.save()
        serializer = self.get_serializer(stuff)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
class WishViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = WishSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        queryset = Favorite.objects.all()
        user_id = self.request.query_params.get('user')

        if user_id is not None:
            queryset = queryset.filter(user=user_id)

        return queryset
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewsSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        product_id = self.request.query_params.get('product', None)
        if product_id:
            return self.queryset.filter(product=product_id)
        return self.queryset

    def perform_create(self, serializer):
        review = serializer.save()

        try:
            stuff = review.product
            keycloak_id = stuff.user  # make sure you have this field

            # Call external API to get user info
            user_info = self.get_user_info_httpx(keycloak_id)
            if user_info is None:
                print(f"User with keycloak_id {keycloak_id} not found via API")
                return

            user_email = user_info.get('email')
            if not user_email:
                print(f"Email not found in user info for keycloak_id {keycloak_id}")
                return

            event_type = 'review.created'
            self.publish_rabbitmq_event(event_type, user_email, review.id)

        except Exception as e:
            print(f"Error processing review create event: {e}")
    

    def get_user_info_httpx(self, keycloak_id):
        url = f"http://192.168.1.120:8000/user/user-details/{keycloak_id}/"
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(url)
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Failed to get user info from API: {response.status_code}")
                    return None
        except httpx.RequestError as e:
            print(f"HTTPX request error: {e}")
            return None

    def publish_rabbitmq_event(self, event_type, email, review_id):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host='host.docker.internal',  # adjust if needed in Docker env
                    port=5672,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            channel = connection.channel()
            exchange_name = 'review_events'
            channel.exchange_declare(exchange=exchange_name, exchange_type='topic', durable=True)
            message = {
                'event': event_type,
                'payload': {
                    'email': email,
                    'review_id': review_id
                }
            }
            channel.basic_publish(
                exchange=exchange_name,
                routing_key=event_type,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            print(f"Published {event_type} for {email}")
        except Exception as e:
            print(f"Failed to publish message: {e}")
        finally:
            if 'connection' in locals() and connection.is_open:
                connection.close()

   
class ImageViewSet(viewsets.ModelViewSet):
    serializer_class = EquipmentImageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = EquipmentImage.objects.all()
        stuff_id = self.request.query_params.get('stuff')

        if stuff_id is not None:
            queryset = queryset.filter(stuff__id=stuff_id)

        return queryset

class StuffManagementViewSet(viewsets.ModelViewSet):
    queryset = StuffManagement.objects.all()
    serializer_class = StuffManagementSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=True, methods=['post'], url_path='available')
    def set_available(self, request, pk=None):
        stuff = self.get_object()
        stuff.availability = 'Available'
        stuff.save()
        serializer = self.get_serializer(stuff)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='unavailable')
    def set_unavailable(self, request, pk=None):
        stuff = self.get_object()
        stuff.availability = 'Unavailable'
        stuff.save()
        serializer = self.get_serializer(stuff)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
class testviewset(viewsets.ModelViewSet):
    queryset = test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [AllowAny]

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Visitor
from .serializers import VisitorSerializer

class VisitorViewSet(viewsets.ModelViewSet):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [AllowAny]

    

    def create(self, request, *args, **kwargs):
        # Ensure the session exists
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        visitor, _ = Visitor.objects.get_or_create(
            session_key=session_key,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )

        serializer = self.get_serializer(visitor)
        return Response(serializer.data, status=status.HTTP_200_OK)
    



class ItemViewViewSet(viewsets.ModelViewSet):
    queryset = ItemView.objects.all()
    serializer_class = ItemViewSerializer
    permission_classes = [AllowAny]

class CartActivityViewSet(viewsets.ModelViewSet):
    queryset = CartActivity.objects.all()
    serializer_class = CartActivitySerializer
    permission_classes = [AllowAny]

class RentalViewSet(viewsets.ModelViewSet):
    queryset = Rental.objects.all()
    serializer_class = RentalSerializer
    permission_classes = [AllowAny]

class SiteStatViewSet(viewsets.ModelViewSet):
    queryset = SiteStat.objects.all()
    serializer_class = SiteStatSerializer
    permission_classes = [AllowAny]

class TrafficSourceViewSet(viewsets.ModelViewSet):
    queryset = TrafficSource.objects.all()
    serializer_class = TrafficSourceSerializer
    permission_classes = [AllowAny]

class DeviceStatViewSet(viewsets.ModelViewSet):
    queryset = DeviceStat.objects.all()
    serializer_class = DeviceStatSerializer
    permission_classes = [AllowAny]

class CategoryStatViewSet(viewsets.ModelViewSet):
    queryset = CategoryStat.objects.all()
    serializer_class = CategoryStatSerializer
    permission_classes = [AllowAny]