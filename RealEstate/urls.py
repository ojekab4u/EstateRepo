from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    # Auth
    path("login", views.UserLogin, name="login"),
    path("logout/", views.log_them_out, name="logout"),
    path('agent-register/', views.agent_register, name='agent_register'),
    path('customer-register/', views.customer_register, name='customer_register'),

    # Public
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('service', views.service, name='service'),
    path('contact', views.contact, name='contact'),
    path('blog', views.blog, name='blog'),
    path('property', views.property_list, name='property_list'),
    path('property_search/', views.property_search, name='property_search'),
    path('<int:pk>/', views.property_detail, name='property_detail'),
    path('<int:property_id>/cost_estimation/', views.cost_estimation_detail, name='cost_estimation_detail'),

    # Agent workspace (agents only)
    path('create/', views.property_create, name='property_create'),
    path('agent/listings/new/', views.property_create, name='property_create_new'),  # alias to canonical name
    path('agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/listings/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('agent/listings/<int:pk>/delete/', views.property_delete, name='property_delete'),

    # Customer workspace
    path('my/estimates/', views.my_estimates, name='my_estimates'),
    path('my/profile/', views.trip_list, name='commute_profile'),
    path('my/trips/add/', views.trip_add, name='trip_add'),
    path('my/trips/<int:pk>/edit/', views.trip_edit, name='trip_edit'),
    path('my/trips/<int:pk>/delete/', views.trip_delete, name='trip_delete'),

    # Vehicles (customers)
    path('addvehicle/', views.add_vehicle, name='add_vehicle'),
    path('my/vehicles/', views.vehicle_list, name='vehicle_list'),
    path('myvehicles/', views.vehicle_list),  # legacy alias
    path('my/vehicles/<int:pk>/edit/', views.edit_vehicle, name='edit_vehicle'),
    path('my/vehicles/<int:pk>/delete/', views.delete_vehicle, name='delete_vehicle'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
