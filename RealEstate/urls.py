from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import (property_list,
                    index,
                    property_detail,
                    property_create, 
                    cost_estimation_detail,
                    property_search,  
                    # cost_estimation,
                    add_vehicle, 
                    vehicle_list,
                    about,service,contact, blog,
                    agent_register, customer_register,
                    )


urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('agent-register/', agent_register, name='agent_register'),
    path('customer-register/',customer_register, name='customer_register'),

    path('', index, name='index'),
    path('about', about, name='about'),
    path('service', service, name='service'),
    path('contact', contact, name='contact'),
    path('blog', blog, name='blog'),
    path('property', property_list, name='property_list'),
    path('create/', property_create, name='property_create'),
    path('<int:pk>/', property_detail, name='property_detail'),
    path('property_search/', property_search, name='property_search'),
    path('<int:property_id>/cost_estimation/', cost_estimation_detail, name='cost_estimation_detail'),
    
    # path('cost-estimation/<int:property_id>/', cost_estimation, name='cost_estimation'),
    # path('property/<int:pk>/', property_detail, name='property_detail'),
    # path('cost-estimation/<int:property_id>/', cost_estimation_detail, name='cost_estimation_detail'),

    
    path('addvehicle/', add_vehicle, name='add_vehicle'),
    path('myvehicles/', vehicle_list, name='vehicle_list'),

]


# if settings.DEBUG:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)