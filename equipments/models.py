from django.db import models
from django.db.models import Sum, Avg, Count
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

class test(models.Model):
    name = models.CharField(max_length=255)
    category=models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategory')
    def __str__(self):
        return self.name

class StuffManagement(models.Model):
    name = models.CharField(max_length=255)
    last_maintenance = models.DateField(blank=True, null=True)
    condition = models.CharField(max_length=50, default="open")
    rental_location = models.CharField(max_length=255, default="nabeul")
    deposit = models.FloatField(blank=True, null=True)
    availability = models.CharField(max_length=255, blank=True, null=True)
    rental_zone = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    contract_required = models.FileField(upload_to='contracts/', blank=True, null=True)

    def __str__(self):
        return self.name

    def utilization_rate(self):
        # Calculate what percentage of time this equipment is rented
        rented_days = self.rental_set.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).aggregate(total_days=Sum('duration'))['total_days'] or 0
        total_days = (timezone.now() - self.created_at).days
        return (rented_days / total_days) * 100 if total_days > 0 else 0

class Stuff(models.Model):
    stuffname = models.CharField(max_length=100)
    short_description = models.CharField(max_length=100, default="open")
    state = models.CharField(max_length=50, default="open")
    status=models.CharField(max_length=50, null=True)
    rental_location = models.CharField(max_length=255, default="nabeul")
    price_per_day = models.FloatField()
    detailed_description = models.TextField()
    location = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='stuffs')
    brand = models.CharField(max_length=255, blank=True, null=True)
    stuff_management = models.ForeignKey(StuffManagement, null=True, blank=True, on_delete=models.SET_NULL, related_name='managed_stuffs')
    user = models.CharField(max_length=255,null=True)
    created_at = models.DateField(auto_now_add=True,null=True)

    def __str__(self):
        return self.stuffname

    class Meta:
        ordering = ['-created_at']

    def total_rentals(self):
        return self.rental_set.count()

    def total_revenue(self):
        return self.rental_set.aggregate(total=Sum('total_price'))['total'] or 0

    def average_rating(self):
        return self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    def view_count(self):
        return self.itemview_set.count()

    def conversion_rate(self):
        views = self.view_count()
        rentals = self.total_rentals()
        return (rentals / views) * 100 if views > 0 else 0

class EquipmentImage(models.Model):
    stuff = models.ForeignKey(Stuff, related_name='equipment_images',null=True, on_delete=models.CASCADE)
    url = models.ImageField(upload_to='equipment_images/')
    alt = models.CharField(max_length=255, blank=True, null=True)
    position = models.PositiveIntegerField()

    def __str__(self):
        return f"Image {self.id} - Position {self.position}"

class Review(models.Model):
    product = models.ForeignKey(Stuff, related_name='reviews', on_delete=models.CASCADE)
    customer = models.CharField(max_length=255)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer} on {self.product}"

    class Meta:
        ordering = ['-created_at']

# ====================== E-COMMERCE STATISTICS MODELS ======================

class Visitor(models.Model):
    session_key = models.CharField(max_length=40, primary_key=True)
    ip_address = models.CharField(max_length=45)
    user_agent = models.TextField()
    first_visit = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Visitor {self.session_key}"
class Favorite(models.Model):
    stuff = models.ForeignKey(Stuff, on_delete=models.CASCADE)
    user = models.CharField(max_length=255,null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
class ItemView(models.Model):
    stuff = models.ForeignKey(Stuff, on_delete=models.CASCADE)
    user = models.CharField(max_length=255,null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=20, choices=[
        ('organic', 'Organic Search'),
        ('direct', 'Direct'),
        ('social', 'Social Media'),
        ('email', 'Email'),
        ('referral', 'Referral'),
        ('paid', 'Paid Ads')
    ])
    device_type = models.CharField(max_length=10, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet')
    ])

    class Meta:
        ordering = ['-timestamp']

class CartActivity(models.Model):
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE)
    stuff = models.ForeignKey(Stuff, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=[
        ('add', 'Add to Cart'),
        ('remove', 'Remove from Cart')
    ])
    timestamp = models.DateTimeField(auto_now_add=True)

class Rental(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    stuff = models.ForeignKey(Stuff, on_delete=models.CASCADE)
    customer = models.IntegerField()  # User ID
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    @property
    def duration(self):
        return (self.end_date - self.start_date).days

    def __str__(self):
        return f"Rental #{self.id} - {self.stuff}"

class SiteStat(models.Model):
    date = models.DateField(unique=True)
    total_visitors = models.PositiveIntegerField(default=0)
    total_page_views = models.PositiveIntegerField(default=0)
    total_rentals = models.PositiveIntegerField(default=0)
    total_revenue = models.FloatField(default=0)
    avg_order_value = models.FloatField(default=0)
    conversion_rate = models.FloatField(default=0)

    class Meta:
        ordering = ['-date']
        verbose_name = "Site Statistics"
        verbose_name_plural = "Site Statistics"

    @classmethod
    def update_daily_stats(cls):
        today = timezone.now().date()
        stats, created = cls.objects.get_or_create(date=today)
        
        # Update visitor stats
        stats.total_visitors = Visitor.objects.filter(
            last_visit__date=today
        ).count()
        
        # Update view stats
        stats.total_page_views = ItemView.objects.filter(
            timestamp__date=today
        ).count()
        
        # Update rental stats
        today_rentals = Rental.objects.filter(created_at__date=today)
        stats.total_rentals = today_rentals.count()
        stats.total_revenue = today_rentals.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        # Calculate conversion rate
        views_today = ItemView.objects.filter(timestamp__date=today).count()
        stats.conversion_rate = (stats.total_rentals / views_today * 100) if views_today > 0 else 0
        
        # Calculate average order value
        stats.avg_order_value = stats.total_revenue / stats.total_rentals if stats.total_rentals > 0 else 0
        
        stats.save()

class TrafficSource(models.Model):
    date = models.DateField()
    source = models.CharField(max_length=20, choices=[
        ('organic', 'Organic Search'),
        ('direct', 'Direct'),
        ('social', 'Social Media'),
        ('email', 'Email'),
        ('referral', 'Referral'),
        ('paid', 'Paid Ads')
    ])
    visitors = models.PositiveIntegerField(default=0)
    rentals = models.PositiveIntegerField(default=0)
    revenue = models.FloatField(default=0)

    class Meta:
        unique_together = ('date', 'source')
        ordering = ['-date', 'source']

class DeviceStat(models.Model):
    date = models.DateField()
    device_type = models.CharField(max_length=10, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet')
    ])
    visitors = models.PositiveIntegerField(default=0)
    rentals = models.PositiveIntegerField(default=0)
    revenue = models.FloatField(default=0)

    class Meta:
        unique_together = ('date', 'device_type')
        ordering = ['-date', 'device_type']

class CategoryStat(models.Model):
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    views = models.PositiveIntegerField(default=0)
    rentals = models.PositiveIntegerField(default=0)
    revenue = models.FloatField(default=0)

    class Meta:
        unique_together = ('date', 'category')
        ordering = ['-date', 'category']