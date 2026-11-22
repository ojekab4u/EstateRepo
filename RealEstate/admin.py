from django.contrib import admin
from .models import Property, PropertyImage, HistoricalData, Vehicle, User, FuelPrice

# Register your models here.

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'address', 'price', 'sale_or_rent',
                    'true_cost_yearly', 'true_cost_computed_at')
    list_filter = ('sale_or_rent', 'property_type')
    search_fields = ('title', 'address')
    inlines = [PropertyImageInline]
    actions = ['recompute_true_cost']

    @admin.action(description="Recompute true cost for selected properties")
    def recompute_true_cost(self, request, queryset):
        done = sum(1 for p in queryset if p.compute_true_cost() is not None)
        self.message_user(request, f"Recomputed true cost for {done} property(ies). "
                                   "Set a fuel price first if none were updated.")

@admin.register(FuelPrice)
class FuelPriceAdmin(admin.ModelAdmin):
    list_display = ('fuel_type', 'price_per_litre', 'effective_date')
    list_filter = ('fuel_type',)

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
