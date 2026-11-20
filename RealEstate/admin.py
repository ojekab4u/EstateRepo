from django.contrib import admin
from .models import Property, PropertyImage, HistoricalData, Vehicle, User

# Register your models here.

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'address', 'price', 'sale_or_rent', 'created_at')
    list_filter = ('sale_or_rent', 'property_type')
    search_fields = ('title', 'address')

@admin.register(HistoricalData)
class HistoricalDataAdmin(admin.ModelAdmin):
    list_display = ('property', 'user', 'total_effective_cost', 'date_field')
    list_filter = ('user',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'fuel_consumption_rate', 'user')
    list_filter = ('user',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_agent', 'is_customer')
    list_filter = ('is_agent', 'is_customer')
    search_fields = ('username', 'email')
