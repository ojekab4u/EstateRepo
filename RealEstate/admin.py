from django.contrib import admin
from .models import Property, PropertyImage,  HistoricalData, Vehicle, User

# Register your models here.

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'address', 'price', 'created_at')
    search_fields = ('title', 'address')
    inlines = [PropertyImageInline]

# @admin.register(CostEstimation)
# class CostEstimationAdmin(admin.ModelAdmin):
#     list_display = ('property', 'commute_distance', 'total_estimated_cost')

@admin.register(HistoricalData)
class HistoricalDataAdmin(admin.ModelAdmin):
    # list_display = ('property', 'date', 'commute_cost')
    list_filter = ('user',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    filter = ('date')

@admin.register(User)
class User(admin.ModelAdmin):
    filter = ('username')