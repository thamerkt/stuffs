from rest_framework.routers import DefaultRouter
from .views import (
    StuffViewSet, CategoryViewSet, ReviewViewSet, ImageViewSet, StuffManagementViewSet, testviewset,
    VisitorViewSet, ItemViewViewSet, CartActivityViewSet, RentalViewSet,
    SiteStatViewSet, TrafficSourceViewSet, DeviceStatViewSet, CategoryStatViewSet,WishViewSet
)
router = DefaultRouter()
urlpatterns = [
    
]
router.register(r'stuffs', StuffViewSet, basename='stuffs')
router.register(r'stuffmanagment', StuffManagementViewSet, basename='stuffmanagment')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'images', ImageViewSet, basename='images')
router.register(r'subcatgeory', testviewset, basename='subcategory')
router.register(r'visitors', VisitorViewSet)
router.register(r'item-views', ItemViewViewSet)
router.register(r'cart-activities', CartActivityViewSet)
router.register(r'rentals', RentalViewSet)
router.register(r'site-stats', SiteStatViewSet)
router.register(r'traffic-sources', TrafficSourceViewSet)
router.register(r'device-stats', DeviceStatViewSet)
router.register(r'category-stats', CategoryStatViewSet,basename="categorystat")
router.register(r'wishlist', WishViewSet)
urlpatterns += router.urls