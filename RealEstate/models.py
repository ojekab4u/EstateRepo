from django.db import models

from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models




class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_agent = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)

    # Agent-specific fields
    passport = models.ImageField(upload_to='agent_passports/', null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    residential_address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.username




PROPERTY_TYPE_CHOICES = [
        ('rent', 'For Rent'),
        ('sale', 'For Sale'),
    ]
class Property(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=255)
    description = models.TextField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)    
    sale_or_rent = models.CharField(max_length=4, choices=PROPERTY_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    property_type = models.CharField(max_length=50, choices=[('Apartment','Apartment'), 
    ('House', 'House'), ('Condo', 'Condo')])
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    square_feet = models.IntegerField()
    # latitude = models.FloatField()
    # longitude = models.FloatField()    
    main_image = models.ImageField(upload_to='property_images/') #THE DIRECTORY
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=now)
    
    def __str__(self):
        return self.title

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/', blank=True) #THE DIRECTORY
    
from django.forms.widgets import FileInput

class MultipleFileInput(FileInput):
    allow_multiple_selected = True

    def render(self, name, value, attrs=None):
        attrs = attrs or {}
        attrs.update({'multiple': True})
        return super().render(name, value, attrs)

    
    def __str__(self):
        return f"Image for {self.property.title}"

class HistoricalData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historical_data')
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    vehicle_name = models.CharField(max_length=255)
    work_location = models.CharField(max_length=255)
    work_trips_per_week = models.IntegerField()
    other_locations = models.TextField()
    total_distance = models.DecimalField(max_digits=10, decimal_places=2)
    transportation_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_effective_cost = models.DecimalField(max_digits=10, decimal_places=2)
    date_field = models.DateTimeField(default=timezone.now)
    
  
class Vehicle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    fuel_consumption_rate = models.FloatField()  # e.g., liters per kilometer

    def __str__(self):
        return self.name

'''

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_histories')
    search_query = models.CharField(max_length=255)
    date_field = models.DateTimeField(default=timezone.now)

class SearchHistory(models.Model):
    user = models.ForeignKey(User, related_name='search_histories', on_delete=models.CASCADE)
    search_query = models.CharField(max_length=255)

    def __str__(self):
        return f"Search by {self.user.username} at {self.created_at}"

class HistoricalData(models.Model):
    user = models.ForeignKey(User, related_name='search_histories', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Historical Data for {self.property.title} on {self.date}"


class CostEstimation(models.Model):
    user = models.ForeignKey(User, related_name='search_histories', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Cost Estimation for {self.property.title}"
        
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='cost_estimation')
    user=user,
            property=property,
            total_distance=total_distance,
            total_transportation_cost=total_transportation_cost,
            total_effective_cost=total_effective_cost,
            current_fuel_price=current_fuel_price,
            details=vehicle_summaries
    commute_distance = models.FloatField()
    commute_cost = models.DecimalField(max_digits=10, decimal_places=2)
    energy_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
'''
    
class UserLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)



