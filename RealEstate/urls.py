from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    # path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path("login", views.Login, name= "login"),
    path("logout/", views.log_them_out, name= "logout"),
    path('agent-register/', views.agent_register, name='agent_register'),
    path('customer-register/',views.customer_register, name='customer_register'),

    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('service', views.service, name='service'),
    path('contact', views.contact, name='contact'),
    path('blog', views.blog, name='blog'),
    path('property', views.property_list, name='property_list'),
    path('create/', views.property_create, name='property_create'),
    path('<int:pk>/', views.property_detail, name='property_detail'),
    path('property_search/', views.property_search, name='property_search'),
    path('<int:property_id>/cost_estimation/', views.cost_estimation_detail, name='cost_estimation_detail'),
    
    # path('cost-estimation/<int:property_id>/', views.cost_estimation, name='cost_estimation'),
    # path('property/<int:pk>/', views.property_detail, name='property_detail'),
    # path('cost-estimation/<int:property_id>/', views.cost_estimation_detail, name='cost_estimation_detail'),

    
    path('addvehicle/', views.add_vehicle, name='add_vehicle'),
    path('myvehicles/', views.vehicle_list, name='vehicle_list'),

]


# if settings.DEBUG:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)