
from django.conf import settings
# from .utils import get_distance
from django.contrib.messages import success, error
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse, HttpResponseRedirect
from .models import Property, PropertyImage, Property, Vehicle
from decimal import Decimal, ROUND_HALF_UP
from .forms import (UserRegistrationForm, 
                    PropertyForm, 
                    PropertySearchForm, 
                    PropertyImageForm,
                    VehicleForm
                    )
from .forms import AgentRegistrationForm, GeneralUserRegistrationForm
from django.urls import reverse_lazy

from django.contrib import messages
from .models import Property, UserLocation, Vehicle
from .utils import( get_distance_matrix, 
                   get_distance_matrix_with_place_id, 
                   get_geocode, 
                   get_route_distance,
                   get_route_distance_from_place_ids,
                   get_place_id
                   )

from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
import random
from django.db.models import Q
from django.core.mail import send_mail
from django.contrib.auth import login, logout, authenticate,  get_user_model


# Create your views here.
def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            request.session['next'] = request.get_full_path()
            return HttpResponseRedirect(reverse_lazy('login'))
        return view_func(request, *args, **kwargs)
    return wrapper


def is_agent(user):
    return user.is_agent

def send_registration_email(user_email):
    send_mail(
        'Welcome to ComfyHome',
        'Thank you for registering with us.',
        'from@example.com',
        [user_email],
        fail_silently=False,
    )

# def agent_register(request):
#     if request.method == 'POST':
#         form = AgentRegistrationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Your account has been successfully created. Please check your email for confirmation.')
#             return redirect('login')  # Redirect to login page or wherever you like
#             # Handle agent registration
#     else:
#         form = AgentRegistrationForm()
#     return render(request, 'register.html', {'agent_form': form})

# def general_user_register(request):
#     if request.method == 'POST':
#         form = GeneralUserRegistrationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             # Handle general user registration
#     else:
#         form = GeneralUserRegistrationForm()
#     return render(request, 'register.html', {'general_user_form': form})



User = get_user_model()
from django.db import IntegrityError

def agent_register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        residential_address = request.POST.get('residential_address')
        password = request.POST.get('password')
        passport = request.FILES.get('passport')

        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('agent_register')

        # Proceed with registration if the email is unique
        user = User.objects.create_user(
            username=email,  # You can use email as the username if required
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            residential_address=residential_address,
            is_agent=True,
        )

        if passport:
            user.passport = passport
            user.save()

        messages.success(request, 'Registration successful! Please check your email to verify your account.')
        return redirect('index')  

    return render(request, 'agent_register.html')

def customer_register(request):
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
        else:
            messages.error(request, 'Sorry, you are already logged in!')
            return render(request, 'customer_register.html', {'next': next_url})

        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'customer_register.html', {'next': next_url})

        try:
            # Create customer user
            user = User.objects.create_user(username=username, email=email, password=password, is_customer=True)
            user.save()

            # Log the user in and redirect to target URL or fallback to index
            login(request, user)
            messages.success(request, f'Dear {username}, Welcome to ComfyHome')
            return redirect(next_url or 'index')

        except IntegrityError:
            messages.error(request, 'There was an error creating your account. Please try again.')
            return render(request, 'customer_register.html', {'next': next_url})

    return render(request, 'customer_register.html', {'next': next_url})


def UserLogin(request):
    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            messages.info(request, f"You are now logged in as {username}.")
            return redirect(next_url or "index")
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'login.html', {'next': next_url})

    return render(request, 'login.html', {'next': next_url})


def log_them_out(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('/')
    # return HttpResponseRedirect('/')




def index(request):
    all_properties = list(Property.objects.all())
    properties = random.sample(all_properties, min(3, len(all_properties)))  # Pick 3 random properties or fewer if there are less than 3
    return render(request, 'homeverse/index.html', {'properties': properties})

def about(request):
    if request.method == "POST":
        pass    
    return render(request, 'homeverse/about.html')

def service(request):
    if request.method == "POST":
        pass
    return render(request, 'homeverse/services.html')


def contact(request):
    if request.method == "POST":
        # Handle form submission logic here
        pass
    return render(request, 'homeverse/contact.html')

def blog(request):
    if request.method == "POST":
        # Handle form submission logic here
        pass
    # posts = BlogPost.objects.all()
    # return render(request, 'blog.html', {'posts': posts})
    return render(request, 'homeverse/blog.html')

def property_list(request):
    sale_or_rent = request.GET.get('sale_or_rent', 'rent')  # Default to 'rent'
    properties = Property.objects.filter(sale_or_rent=sale_or_rent)
    query = request.GET.get('q', '')

    # Optional: Implement filtering by price, bedrooms, etc.
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    bedrooms = request.GET.get('bedrooms')
    bathrooms = request.GET.get('bathrooms')

    if query:
        properties = properties.filter(title__icontains=query)
    if price_min:
        properties = properties.filter(price__gte=price_min)
    if price_max:
        properties = properties.filter(price__lte=price_max)
    if bedrooms:
        properties = properties.filter(bedrooms=bedrooms)
    if bathrooms:
        properties = properties.filter(bathrooms=bathrooms)

    context = {
        'properties': properties,
        'query': query,
        'price_min': price_min,
        'price_max': price_max,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'sale_or_rent': sale_or_rent,
    }
    return render(request, 'property_list.html', context)


def property_search(request):
    query = request.GET.get('q')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    bedrooms = request.GET.get('bedrooms')
    bathrooms = request.GET.get('bathrooms')

    properties = Property.objects.all()

    if query:
        properties = properties.filter(
            title__icontains=query
        ) | properties.filter(
            description__icontains=query
        ) | properties.filter(
            address__icontains=query
        ) | properties.filter(
            city__icontains=query
        ) | properties.filter(
            state__icontains=query
        )
    if price_min:
        properties = properties.filter(price__gte=price_min)    
    if price_max:
        properties = properties.filter(price__lte=price_max)    
    if bedrooms:
        properties = properties.filter(bedrooms__gte=bedrooms)    
    if bathrooms:
        properties = properties.filter(bathrooms__gte=bathrooms)
    context = {
        'properties': properties,
        'query': query,
        'price_min': price_min,
        'price_max': price_max,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms    }
    return render(request, 'property_search.html', context)




def property_detail(request, pk):
    property = get_object_or_404(Property, pk=pk)
    place_type = request.GET.get('place_type')  # Gets 'market' or other place types
    images = property.images.all()
    google_api_key = settings.GOOGLE_API_KEY

    context = {
        'property': property,
        'place_type': place_type,
        'images': images,
        'google_api_key': google_api_key
    }
    
    return render(request, 'property_detail.html', context)

def agent_required(user):
    return user.is_authenticated and user.is_agent

@login_required
def property_create(request):
    if not request.user.is_agent:
        messages.info(request, "Please login with agency credentials.")
        return redirect('login')  # Redirect to a different page or show an error message
    

    if request.method == 'POST':
        google_api_key = settings.GOOGLE_API_KEY
        property_form = PropertyForm(request.POST, request.FILES)
        images = request.FILES.getlist('additional_images')

        if property_form.is_valid():
            property = property_form.save(commit=False)
            property.owner = request.user
            property.save()

            for image in images:
                PropertyImage.objects.create(property=property, image=image)

            messages.success(request, 'Property created successfully!')
            return redirect('property_list')  
    else:
        property_form = PropertyForm()

    return render(request, 'property_form.html', {
        'form': property_form, 'google_api_key': settings.GOOGLE_API_KEY,
    })
    
    
    
# def property_search(request):
#     if request.method == 'POST':
#         form = PropertySearchForm(request.POST)
#         if form.is_valid():
#             search_query = form.cleaned_data.get('search_query')
#             min_price = form.cleaned_data.get('min_price')
#             max_price = form.cleaned_data.get('max_price')
#             address = form.cleaned_data.get('address')

#             properties = Property.objects.all()

#             if search_query:
#                 properties = properties.filter(title__icontains=search_query)

#             if min_price is not None:
#                 properties = properties.filter(price__gte=min_price)

#             if max_price is not None:
#                 properties = properties.filter(price__lte=max_price)

#             if address:
#                 properties = properties.filter(address__icontains=address)

#             return render(request, 'property_search_results.html', {
#                 'properties': properties,
#                 'query': search_query,
#                 'min_price': min_price,
#                 'max_price': max_price,
#                 'address': address,
#             })
#     else:
#         form = PropertySearchForm()

#     return render(request, 'property_search.html', {'form': form})

    
    
@login_required
def add_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.user = request.user
            vehicle.save()
            return redirect('vehicle_list')
    else:
        form = VehicleForm()
    return render(request, 'add_vehicle.html', {'form': form})

@login_required
def vehicle_list(request):
    vehicles = Vehicle.objects.filter(user=request.user)
    return render(request, 'vehicle_list.html', {'vehicles': vehicles})


'''
@login_required
def cost_estimation_detail(request, property_id):
    # if request.user.is_agent:
    #     return redirect('home')  # Agents should not be able to make cost estimations

    property = get_object_or_404(Property, pk=property_id)
    google_api_key = settings.GOOGLE_API_KEY
    user = request.user
    vehicles = Vehicle.objects.filter(user=user)

    if request.method == 'POST':
        # Retrieve form data
        num_cars = int(request.POST.get('num_cars', 1))  # Default to 1 if not provided
        car_details = []

        # Collect details for each car
        for i in range(1, num_cars + 1):
            car_details.append({
                'vehicle_id': request.POST.get(f'vehicle_{i}'),
                'work_location': request.POST.get(f'work_location_{i}'),
                'work_trips_per_week': int(request.POST.get(f'work_trips_per_week_{i}', 5)),  # Default to 5 trips/week
                'other_locations': request.POST.get(f'other_locations_{i}', '')
            })

        # Parse the current fuel price
        current_fuel_price = request.POST.get('current_fuel_price')
        if current_fuel_price:
            current_fuel_price = Decimal(current_fuel_price)
        else:
            current_fuel_price = Decimal(0)  # Set a default value if None

        # Initialize variables to aggregate the results
        vehicle_summaries = []
        total_transportation_cost = Decimal(0)
        total_distance = Decimal(0)

        # Iterate over each car's details
        for car in car_details:
            vehicle = get_object_or_404(Vehicle, pk=car['vehicle_id'])
            fuel_consumption_rate = Decimal(vehicle.fuel_consumption_rate)
            work_trips_per_week = car['work_trips_per_week']
            work_round_trips_per_year = work_trips_per_week * 52  # 52 weeks in a year

            # Get Place IDs for the property address and work location
            property_address = f"{property.address}, {property.city}, {property.state}, {property.zip_code}"
            property_place_id = get_place_id(property_address, google_api_key)
            work_place_id = get_place_id(car['work_location'], google_api_key)

            # Print Place IDs and addresses for debugging
            print(f"Property Address: {property_address}")
            print(f"Property Place ID: {property_place_id}")
            print(f"Work Location: {car['work_location']}")
            print(f"Work Place ID: {work_place_id}")

            if property_place_id and work_place_id:
                # Use Place IDs for route distance calculation
                work_distance_in_kilometers = get_route_distance_from_place_ids(property_place_id, work_place_id, google_api_key)
                if work_distance_in_kilometers is not None:
                    work_distance_in_kilometers = Decimal(work_distance_in_kilometers)
                else:
                    work_distance_in_kilometers = Decimal(0)  # Handle None as 0
            else:
                work_distance_in_kilometers = Decimal(0)  # Set to 0 if Place ID lookup fails

            # Print distance for debugging
            print(f"Work Distance (in km): {work_distance_in_kilometers}")

            # Calculate total distance for work (considering round trips per year)
            total_work_distance = work_distance_in_kilometers * Decimal(work_round_trips_per_year)
            total_distance += total_work_distance

            # Handle other locations
            if car['other_locations']:
                other_locations_list = car['other_locations'].split(',')
                for location in other_locations_list:
                    location_details = location.strip().split(':')  # Expecting format: "Address:trips_per_week"
                    if len(location_details) == 2:
                        location_address, trips_per_week = location_details
                        trips_per_week = int(trips_per_week)
                        round_trips_per_year = trips_per_week * 52  # Convert to yearly trips

                        # Get Place ID for the other location
                        loc_place_id = get_place_id(location_address.strip(), google_api_key)
                        if loc_place_id:
                            distance_in_kilometers = get_route_distance_from_place_ids(property_place_id, loc_place_id, google_api_key)
                            if distance_in_kilometers is not None:
                                distance_in_kilometers = Decimal(distance_in_kilometers)
                            else:
                                distance_in_kilometers = Decimal(0)  # Handle None as 0
                        else:
                            distance_in_kilometers = Decimal(0)  # Set to 0 if Place ID lookup fails

                        # Print other location details for debugging
                        print(f"Other Location Address: {location_address.strip()}")
                        print(f"Other Location Place ID: {loc_place_id}")
                        print(f"Other Location Distance (in km): {distance_in_kilometers}")

                        total_distance += distance_in_kilometers * Decimal(round_trips_per_year)

            # Calculate transportation cost for this vehicle
            transportation_cost = total_distance * fuel_consumption_rate * current_fuel_price
            total_transportation_cost += transportation_cost

            # Store summary for each vehicle
            vehicle_summaries.append({
                'name': vehicle.name,
                'work_location': car['work_location'],
                'work_trips_per_week': work_trips_per_week,
                'other_locations': car['other_locations'],
                'total_distance': total_distance,
                'transportation_cost': transportation_cost
            })

        # Calculate the total effective cost
        total_effective_cost = property.price + total_transportation_cost

    
        # Render the result on the same page
        context = {
            'property': property,
            'vehicles': vehicles,
            'vehicle_summaries': vehicle_summaries,
            'total_distance': total_distance,
            'total_transportation_cost': total_transportation_cost,
            'total_effective_cost': total_effective_cost,
            'current_fuel_price': current_fuel_price,
            'google_api_key': settings.GOOGLE_API_KEY,
        }
        return render(request, 'cost_estimation_detail.html', context)

    context = {
        'property': property,
        'vehicles': vehicles,
        'google_api_key': settings.GOOGLE_API_KEY,
    }
    return render(request, 'cost_estimation_detail.html', context)
'''

import json
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from decimal import Decimal, InvalidOperation
from .models import Property, Vehicle, HistoricalData
from .utils import get_place_id, get_route_distance_from_place_ids

logger = logging.getLogger(__name__)

'''
@login_required
def cost_estimation_detail(request, property_id):
    property = get_object_or_404(Property, pk=property_id)
    google_api_key = settings.GOOGLE_API_KEY
    user = request.user
    vehicles = Vehicle.objects.filter(user=user)    

    # Geocode the property address to get lat/lng
    property_address = f"{property.address}, {property.city}, {property.state}, {property.zip_code}"
    property_lat_lng = get_geocode(property_address, google_api_key)

    house_lat = property_lat_lng['lat']
    house_lng = property_lat_lng['lng']

    # Initialize variables to avoid UnboundLocalError
    work_location = None
    vehicle_distances = {}
    if request.user.is_agent:
        return redirect('index')  # Redirect to a different page or show an error message

    if request.method == 'POST':
        try:
            num_cars = int(request.POST.get('num_cars', 1))  # Default to 1 if not provided
        except ValueError:
            return HttpResponse("Invalid number of cars. Please provide a valid number.")
        
        car_details = []

        # Collect details for each car
        for i in range(1, num_cars + 1):
            vehicle_id = request.POST.get(f'vehicle_{i}')
            work_location = request.POST.get(f'work_location_{i}')
            try:
                work_trips_per_week = int(request.POST.get(f'work_trips_per_week_{i}', 5))  # Default to 5 trips/week
            except ValueError:
                work_trips_per_week = 5  # Fallback to default

            other_locations = []
            j = 0
            while True:
                location_name = request.POST.get(f'location_name_{i}_{j}')
                if not location_name:
                    break
                location_address = request.POST.get(f'location_address_{i}_{j}')
                try:
                    trips_per_week = int(request.POST.get(f'location_trips_per_week_{i}_{j}', 0))
                except ValueError:
                    trips_per_week = 0  # Default to 0 if invalid
                other_locations.append({
                    'name': location_name,
                    'address': location_address,
                    'trips_per_week': trips_per_week
                })
                j += 1

            car_details.append({
                'vehicle_id': vehicle_id,
                'work_location': work_location,
                'work_trips_per_week': work_trips_per_week,
                'other_locations': other_locations
            })

        # Ensure fuel price is valid
        current_fuel_price = request.POST.get('current_fuel_price')
        try:
            current_fuel_price = Decimal(current_fuel_price) if current_fuel_price else Decimal(0)
        except InvalidOperation:
            return HttpResponse("Invalid fuel price. Please enter a valid number.")

        vehicle_summaries = []
        total_transportation_cost = Decimal(0)
        total_distance_for_vehicle_to_other_loc =  (0)
        

        # Iterate over each car's details
        for car in car_details:
            vehicle = get_object_or_404(Vehicle, pk=car['vehicle_id'])
            fuel_consumption_rate = Decimal(vehicle.fuel_consumption_rate)
            work_trips_per_week = car['work_trips_per_week']
            work_round_trips_per_year = work_trips_per_week * 52  # Multiply by 52 for yearly calculation

            property_place_id = get_place_id(property_address, google_api_key)
            work_place_id = get_place_id(car['work_location'], google_api_key)

            total_distance_for_vehicle = Decimal(0)  # Reset for each vehicle
            total_distance_to_work_and_other_loc=Decimal(0)

            # Calculate round-trip distance for work location
            if property_place_id and work_place_id:
                work_distance_in_kilometers = get_route_distance_from_place_ids(property_place_id, work_place_id, google_api_key)
                if work_distance_in_kilometers is not None:
                    try:
                        work_distance_in_kilometers = Decimal(work_distance_in_kilometers) * 2  # Multiply by 2 for round-trip
                    except InvalidOperation:
                        work_distance_in_kilometers = Decimal(0)  # Default to 0 if invalid
                else:
                    work_distance_in_kilometers = Decimal(0)
            else:
                work_distance_in_kilometers = Decimal(0)

            # Total work distance for the year
            total_work_distance = work_distance_in_kilometers * Decimal(work_round_trips_per_year)
            # total_distance_for_vehicle += total_work_distance
            
            total_distance_for_vehicle_to_work = total_work_distance
            

            # Calculate round-trip distance for other locations
            for location in car['other_locations']:
                location_address = location['address']
                trips_per_week = location['trips_per_week']
                round_trips_per_year = trips_per_week * 52  # Multiply by 52 for yearly calculation

                loc_place_id = get_place_id(location_address, google_api_key)
                if loc_place_id:
                    distance_in_kilometers = get_route_distance_from_place_ids(property_place_id, loc_place_id, google_api_key)
                    if distance_in_kilometers is not None:
                        try:
                            distance_in_kilometers = Decimal(distance_in_kilometers) * 2  # Multiply by 2 for round-trip
                        except InvalidOperation:
                            distance_in_kilometers = Decimal(0)  # Default to 0 if invalid
                    else:
                        distance_in_kilometers = Decimal(0)
                else:
                    distance_in_kilometers = Decimal(0)

                total_distance_for_vehicle += distance_in_kilometers * Decimal(round_trips_per_year)
                
                total_distance_for_vehicle_to_other_loc =  total_distance_for_vehicle
            # Calculate transportation cost for this vehicle (fuel consumption)
            total_distance_to_work_and_other_loc = total_distance_for_vehicle_to_work + total_distance_for_vehicle_to_other_loc
            transportation_cost = total_distance_to_work_and_other_loc * fuel_consumption_rate * current_fuel_price
            total_transportation_cost += transportation_cost

            vehicle_distances[vehicle.name] = total_distance_to_work_and_other_loc 
            
            vehicle_distances[vehicle.name] = {
                'weekly': total_distance_for_vehicle / 52,
                'monthly': total_distance_for_vehicle / 12,
                'yearly': total_distance_for_vehicle
            }
            
            vehicle_summaries.append({
                'vehicle_name': vehicle.name,
                'work_location': car['work_location'],
                'work_trips_per_week': work_trips_per_week,
                'other_locations': ', '.join([f"{loc['name']}: {loc['trips_per_week']}" for loc in car['other_locations']]),
                'total_distance': total_distance_to_work_and_other_loc,
                'transportation_cost': transportation_cost
            })
            
            # vehicle_summary = {
            #     'vehicle_name': vehicle.name,
            #     'total_distance_weekly': total_distance_for_vehicle / 52,
            #     'total_distance_monthly': total_distance_for_vehicle / 12,
            #     'total_distance_yearly': total_distance_for_vehicle,
            #     'weekly_estimate': total_distance_for_vehicle / 52 * fuel_consumption_rate * current_fuel_price,
            #     'monthly_estimate': total_distance_for_vehicle / 12 * fuel_consumption_rate * current_fuel_price,
            #     'yearly_estimate': total_distance_for_vehicle * fuel_consumption_rate * current_fuel_price
            # }

        total_effective_cost = property.price + total_transportation_cost

        # Save historical data
      
        for car in car_details:
            HistoricalData.objects.create(
                user=user,
                property=property,
                vehicle_name=Vehicle.objects.get(id=car['vehicle_id']).name,
                work_location=car['work_location'],
                work_trips_per_week=car['work_trips_per_week'],
                other_locations=json.dumps(car['other_locations']),
                total_distance=total_distance_for_vehicle,
                transportation_cost=total_transportation_cost,
                total_effective_cost=total_effective_cost
            )
        

                # Calculate weekly, monthly, and yearly estimates
        yearly_distance_for_vehicle = total_distance_to_work_and_other_loc
        monthly_distance_for_vehicle = yearly_distance_for_vehicle / 12
        weekly_distance_for_vehicle = yearly_distance_for_vehicle / 52

        weekly_transportation_cost = total_transportation_cost / 52
        monthly_transportation_cost = total_transportation_cost / 12
        yearly_transportation_cost = total_transportation_cost

        weekly_rent = property.price / 52
        monthly_rent = property.price / 12
        yearly_rent = property.price

        # Effective cost
        weekly_effective_cost = weekly_rent + weekly_transportation_cost
        monthly_effective_cost = monthly_rent + monthly_transportation_cost
        yearly_effective_cost = yearly_rent + yearly_transportation_cost

        # Print results to the console
        print(f"Total Distance in km: {total_distance_to_work_and_other_loc}")
        print(f"Weekly Transportation Cost: {weekly_transportation_cost}")
        print(f"Monthly Transportation Cost: {monthly_transportation_cost}")
        print(f"Yearly Transportation Cost: {yearly_transportation_cost}")
        print(f"Weekly Effective Cost: {weekly_effective_cost}")
        print(f"Monthly Effective Cost: {monthly_effective_cost}")
        print(f"Yearly Effective Cost: {yearly_effective_cost}")

        # Render the result on the same page
         
        context = {
            'property': property,
            'vehicles': vehicles,
            'vehicle_summaries': vehicle_summaries,
            'total_transportation_cost': total_transportation_cost,
            'total_effective_cost': total_effective_cost,
            # 'weekly_estimate': weekly_estimate,
            # 'monthly_estimate': monthly_estimate,
            # 'yearly_estimate': yearly_estimate,
            'google_api_key': settings.GOOGLE_API_KEY,
            'yearly_effective_cost':yearly_effective_cost,
            'monthly_effective_cost':monthly_effective_cost,
            'weekly_effective_cost':weekly_effective_cost       
            }
        context.update({
            'weekly_distance_for_vehicle': weekly_distance_for_vehicle,
            'monthly_distance_for_vehicle': monthly_distance_for_vehicle,
            'yearly_distance_for_vehicle': yearly_distance_for_vehicle,
            'total_transportation_cost_weekly': weekly_transportation_cost,
            'total_transportation_cost_monthly': monthly_transportation_cost,
            'total_transportation_cost_yearly': yearly_transportation_cost,
            'rent_weekly': weekly_rent,
            'rent_monthly': monthly_rent,
            'rent_yearly': yearly_rent,
            'effective_cost_weekly': weekly_effective_cost,
            'effective_cost_monthly': monthly_effective_cost,
            'effective_cost_yearly': yearly_effective_cost
        })
        return render(request, 'cost_estimation_detail.html', context)

    else:
        context = {
            'property': property,
            'vehicles': vehicles,
            'google_api_key': settings.GOOGLE_API_KEY
        }
        return render(request, 'cost_estimation_detail.html', context)

'''
@login_required
def cost_estimation_detail(request, property_id):
    property = get_object_or_404(Property, pk=property_id)
    google_api_key = settings.GOOGLE_API_KEY
    user = request.user
    vehicles = Vehicle.objects.filter(user=user)    
    
    # Geocode the property address to get lat/lng
    property_address = f"{property.address}, {property.city}, {property.state}, {property.zip_code}"
    property_lat_lng = get_geocode(property_address, google_api_key)

    house_lat = property_lat_lng['lat']
    house_lng = property_lat_lng['lng']

    if request.user.is_agent:
        messages.info(request, "Agents are not allowed to use estimator")
        return redirect('index')  # Redirect agents to a different page as per your logic

    if request.method == 'POST':
        num_cars = int(request.POST.get('num_cars', 1))  # Default to 1 if not provided
        car_details = []

        # Collect details for each car
        for i in range(1, num_cars + 1):
            vehicle_id = request.POST.get(f'vehicle_{i}')
            work_location = request.POST.get(f'work_location_{i}')
            work_trips_per_week = int(request.POST.get(f'work_trips_per_week_{i}', 5))  # Default to 5 trips/week
            other_locations = []

            # Collect other locations for each car
            j = 0
            while True:
                location_name = request.POST.get(f'location_name_{i}_{j}')
                if not location_name:
                    break
                location_address = request.POST.get(f'location_address_{i}_{j}')
                trips_per_week = int(request.POST.get(f'location_trips_per_week_{i}_{j}', 0))
                other_locations.append({
                    'name': location_name,
                    'address': location_address,
                    'trips_per_week': trips_per_week
                })
                j += 1

            car_details.append({
                'vehicle_id': vehicle_id,
                'work_location': work_location,
                'work_trips_per_week': work_trips_per_week,
                'other_locations': other_locations
            })

        # Ensure fuel price is valid
        current_fuel_price = request.POST.get('current_fuel_price')
        try:
            current_fuel_price = Decimal(current_fuel_price) if current_fuel_price else Decimal(0)
        except InvalidOperation:
            return HttpResponse("Invalid fuel price. Please enter a valid number.")

        # Initialize total distance for all vehicles
        total_distance_all_vehicles_yearly = Decimal(0)
        # Initialize individual vehicle distance mapping
        vehicle_distances = {}
        vehicle_summaries = []
        total_transportation_cost = Decimal(0)

        # Iterate over each car's details
        for car in car_details:
            vehicle = get_object_or_404(Vehicle, pk=car['vehicle_id'])
            fuel_consumption_rate = Decimal(vehicle.fuel_consumption_rate)
            work_trips_per_week = car['work_trips_per_week']
            work_round_trips_per_year = work_trips_per_week * 52  # Multiply by 52 for yearly calculation

            property_place_id = get_place_id(property_address, google_api_key)
            work_place_id = get_place_id(car['work_location'], google_api_key)

            total_distance_for_vehicle = Decimal(0)
            

            # Calculate round-trip distance for work location
            work_distance_in_kilometers = get_route_distance_from_place_ids(property_place_id, work_place_id, google_api_key)
            work_distance_in_kilometers = Decimal(work_distance_in_kilometers) * 2 if work_distance_in_kilometers else Decimal(0)
            total_work_distance = work_distance_in_kilometers * Decimal(work_round_trips_per_year)
            total_distance_for_vehicle += total_work_distance
            
            # total_distance_for_vehicle_to_work = total_work_distance
            
            # Calculate round-trip distance for other locations
            for location in car['other_locations']:
                loc_place_id = get_place_id(location['address'], google_api_key)
                distance_in_kilometers = get_route_distance_from_place_ids(property_place_id, loc_place_id, google_api_key)
                distance_in_kilometers = Decimal(distance_in_kilometers) * 2 if distance_in_kilometers else Decimal(0)
                trips_per_week = location['trips_per_week']
                total_distance_for_vehicle += distance_in_kilometers * Decimal(trips_per_week * 52)
                
            # total_distance_for_vehicle_to_Other_place = total_distance_for_vehicle
                
            vehicle_distances[vehicle.name] = total_distance_for_vehicle

            # Add the yearly distance for this vehicle to the total distance across all vehicles
            total_distance_all_vehicles_yearly += total_distance_for_vehicle
            # total_distance_all_vehicles_work_and_other_place_yearly = total_distance_for_vehicle_to_Other_place + total_distance_for_vehicle_to_work

            
            vehicle_distances[vehicle.name] = {
                'weekly': total_distance_for_vehicle / 52,
                'monthly': total_distance_for_vehicle / 12,
                'yearly': total_distance_for_vehicle
            }

            # Split the distance for weekly, monthly, and yearly
            vehicle_summary = {
                'vehicle_name': vehicle.name,
                'total_distance_weekly': total_distance_for_vehicle / 52,
                'total_distance_monthly': total_distance_for_vehicle / 12,
                'total_distance_yearly': total_distance_for_vehicle,
                'weekly_estimate': total_distance_for_vehicle / 52 * fuel_consumption_rate * current_fuel_price,
                'monthly_estimate': total_distance_for_vehicle / 12 * fuel_consumption_rate * current_fuel_price,
                'yearly_estimate': total_distance_for_vehicle * fuel_consumption_rate * current_fuel_price
            }

            vehicle_summaries.append(vehicle_summary)
            total_transportation_cost += vehicle_summary['yearly_estimate']

        # Calculate rent on a weekly, monthly, and yearly basis
        rent_weekly = property.price / 52
        rent_monthly = property.price / 12
        rent_yearly = property.price

        
        
        
        for vehicle_name, distance in vehicle_distances.items():
            if vehicle_name:
                print(f"Total Distance Covered by {vehicle_name}: {distance} km")
        total_distance_covered_ForALL = sum(distance['yearly'] for distance in vehicle_distances.values())
        print(f"Total Distance Covered by all Vehicles: {total_distance_covered_ForALL} km")
        print(f"Total Transportation Cost for all Vehicles: {total_transportation_cost}")
        
        yearly_distance_for_vehicle = total_distance_covered_ForALL
        weekly_distance_for_vehicle = yearly_distance_for_vehicle / 52 
        monthly_distance_for_vehicle = yearly_distance_for_vehicle/12 
        
        
        # Final_total_transportation_cost = total_distance_covered_ForALL*fuel_consumption_rate * current_fuel_price
        
        total_transportation_cost_yearly = total_transportation_cost
        total_transportation_cost_monthly = total_transportation_cost/12
        total_transportation_cost_weekly = total_transportation_cost/52
        
        # Calculate effective cost (rent + transportation)
        effective_cost_weekly = rent_weekly + total_transportation_cost_weekly
        effective_cost_monthly = rent_monthly + total_transportation_cost_monthly
        effective_cost_yearly = rent_yearly +total_transportation_cost_yearly
        
        # Prepare the context for the template
        context = {
            'property': property,
            'vehicle_summaries': vehicle_summaries,
            'rent_weekly': rent_weekly,
            'rent_monthly': rent_monthly,
            'rent_yearly': rent_yearly,
            'effective_cost_weekly': effective_cost_weekly,
            'effective_cost_monthly': effective_cost_monthly,
            'effective_cost_yearly': effective_cost_yearly,
            'total_transportation_cost_yearly': total_transportation_cost_yearly,
            'total_transportation_cost_monthly': total_transportation_cost_monthly,
            'total_transportation_cost_weekly':  total_transportation_cost_weekly,
            'weekly_distance_for_vehicle': weekly_distance_for_vehicle,
            'monthly_distance_for_vehicle': monthly_distance_for_vehicle,
            'yearly_distance_for_vehicle': total_distance_covered_ForALL,
            'vehicle_distances': vehicle_distances  
        }

        # print(f"Vehicle: {vehicle.name}")
        # print(f"Total Work Distance (Yearly): {total_work_distance}")
        # print(f"Total Distance (Yearly) for Vehicle: {total_distance_for_vehicle}")
        # print(f"Work Place ID: {work_place_id}")
        # print(f"Work Distance (in km): {work_distance_in_kilometers}")
        return render(request, 'cost_estimation_detail.html', context)

    # Provide initial context when loading the page
    context = {
        'property': property,
        'vehicles': vehicles,
        'house_lat': house_lat,
        'house_lng': house_lng, 
        'google_api_key': settings.GOOGLE_API_KEY
    }
    
    return render(request, 'cost_estimation_detail.html', context)







'''''
@login_required
def cost_estimation_detail(request, property_id):
    property = get_object_or_404(Property, pk=property_id)
    user = request.user
    vehicles = Vehicle.objects.filter(user=user)
    user_locations = UserLocation.objects.filter(user=user)

    if request.method == 'POST':
        # Retrieve form data
        work_location = request.POST.get('work_location')
        work_location_place_id = request.POST.get('work_location_place_id')  # Capture Place ID for work location
        work_trips_per_week = int(request.POST.get('work_trips_per_week', 5))  # Default to 5 trips/week
        other_locations = request.POST.get('other_locations', '')
        vehicle_id = request.POST.get('vehicle')
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        fuel_consumption_rate = Decimal(vehicle.fuel_consumption_rate)  # Convert to Decimal
        current_fuel_price = Decimal(request.POST.get('current_fuel_price'))  # Convert to Decimal

        # Calculate annual trips (considering 52 weeks in a year)
        work_round_trips_per_year = work_trips_per_week * 52

        # Geocode the property address
        property_address = f"{property.address}, {property.city}, {property.state}, {property.zip_code}"
        property_lat, property_lng = get_geocode(property_address, google_api_key)

        # Use Place ID for the work location if available
        if work_location_place_id:
            work_distance_matrix = get_distance_matrix_with_place_id(f"{property_lat},{property_lng}", work_location_place_id, google_api_key)
        else:
            # Fallback to address-based geocoding if Place ID is not available
            work_lat, work_lng = get_geocode(work_location, google_api_key)
            if property_lat and property_lng and work_lat and work_lng:
                origin = f"{property_lat},{property_lng}"
                destination = f"{work_lat},{work_lng}"
                work_distance_matrix = get_distance_matrix(origin, destination, google_api_key)
            else:
                work_distance_matrix = get_distance_matrix(property_address, work_location, google_api_key)

        work_distance = Decimal(0)
        if work_distance_matrix and work_distance_matrix.get('rows'):
            elements = work_distance_matrix['rows'][0].get('elements')
            if elements and elements[0].get('distance'):
                work_distance = Decimal(elements[0]['distance']['value']) / Decimal(1000)  # Convert to km

        # Calculate total distance for work (considering round trips)
        total_work_distance = work_distance * work_round_trips_per_year
        total_distance = total_work_distance

        # Handle other locations
        if other_locations:
            other_locations_list = other_locations.split(',')
            for location in other_locations_list:
                location_details = location.strip().split(':')  # Expecting format: "Address:trips_per_week"
                if len(location_details) == 2:
                    location_address, trips_per_week = location_details
                    trips_per_week = int(trips_per_week)
                    round_trips_per_year = trips_per_week * 52  # Convert to annual trips

                    # Capture Place ID for other locations
                    location_place_id = request.POST.get(f'{location_address}_place_id')

                    if location_place_id:
                        distance_matrix = get_distance_matrix_with_place_id(f"{property_lat},{property_lng}", location_place_id, google_api_key)
                    else:
                        loc_lat, loc_lng = get_geocode(location_address.strip(), google_api_key)
                        if loc_lat and loc_lng:
                            other_origin = f"{property_lat},{property_lng}"
                            other_destination = f"{loc_lat},{loc_lng}"
                            distance_matrix = get_distance_matrix(other_origin, other_destination, google_api_key)
                        else:
                            distance_matrix = get_distance_matrix(property_address, location_address.strip(), google_api_key)

                    if distance_matrix and distance_matrix.get('rows'):
                        elements = distance_matrix['rows'][0].get('elements')
                        if elements and elements[0].get('distance'):
                            distance = Decimal(elements[0]['distance']['value']) / Decimal(1000)  # Convert to km
                            total_distance += distance * round_trips_per_year

        # Calculate total transportation cost and total effective cost
        total_transportation_cost = total_distance * fuel_consumption_rate * current_fuel_price
        total_effective_cost = property.price + total_transportation_cost

        # Render the result on the same page
        context = {
            'property': property,
            'vehicles': vehicles,
            'total_distance': total_distance,
            'total_transportation_cost': total_transportation_cost,
            'total_effective_cost': total_effective_cost,
            'work_location': work_location,
            'work_trips_per_week': work_trips_per_week,
            'other_locations': other_locations,
            'current_fuel_price': current_fuel_price
        }
        return render(request, 'cost_estimation_detail.html', context)

    context = {
        'property': property,
        'vehicles': vehicles,
    }
    return render(request, 'cost_estimation_detail.html', context)
'''''

'''
@login_required
def cost_estimation_detail(request, property_id):
    property = get_object_or_404(Property, pk=property_id)
    user = request.user
    vehicles = Vehicle.objects.filter(user=user)
    user_locations = UserLocation.objects.filter(user=user)

    if request.method == 'POST':
        # Retrieve form data
        work_location = request.POST.get('work_location')
        work_trips_per_week = int(request.POST.get('work_trips_per_week', 5))  # Default to 5 trips/week
        other_locations = request.POST.get('other_locations', '')
        vehicle_id = request.POST.get('vehicle')
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        fuel_consumption_rate = Decimal(vehicle.fuel_consumption_rate)  # Convert to Decimal
        current_fuel_price = Decimal(request.POST.get('current_fuel_price'))  # Convert to Decimal

        # Calculate trips per year
        work_round_trips_per_year = work_trips_per_week * 52  # 52 weeks in a year

        # Geocode the property address
        property_address = f"{property.address}, {property.city}, {property.state}, {property.zip_code}"
        property_lat, property_lng = get_geocode(property_address, google_api_key)

        # Geocode the work location
        work_lat, work_lng = get_geocode(work_location, google_api_key)

        # Calculate work distance
        work_distance = Decimal(0)
        if property_lat and property_lng and work_lat and work_lng:
            work_distance_matrix = get_distance_matrix((property_lat, property_lng), (work_lat, work_lng), google_api_key)
            if work_distance_matrix and work_distance_matrix.get('rows'):
                elements = work_distance_matrix['rows'][0].get('elements')
                if elements and elements[0].get('distance'):
                    raw_distance = elements[0]['distance']['value']  # Distance in meters
                    print(f"Raw distance in meters: {raw_distance}")
                    work_distance = Decimal(raw_distance) / Decimal(1000)  # Convert to kilometers
                    print(f"Converted distance in kilometers: {work_distance}")

        # Calculate total distance for work (considering round trips per year)
        total_work_distance = work_distance * work_round_trips_per_year
        total_distance = total_work_distance

        # Handle other locations
        if other_locations:
            other_locations_list = other_locations.split(',')
            for location in other_locations_list:
                location_details = location.strip().split(':')  # Expecting format: "Address:trips_per_week"
                if len(location_details) == 2:
                    location_address = location_details[0].strip()
                    trips_per_week = int(location_details[1].strip())
                    round_trips_per_year = trips_per_week * 52  # Convert to yearly trips

                    # Geocode the other location
                    loc_lat, loc_lng = get_geocode(location_address, google_api_key)
                    if loc_lat and loc_lng:
                        distance_matrix = get_distance_matrix((property_lat, property_lng), (loc_lat, loc_lng), google_api_key)
                        if distance_matrix and distance_matrix.get('rows'):
                            elements = distance_matrix['rows'][0].get('elements')
                            if elements and elements[0].get('distance'):
                                distance = Decimal(elements[0]['distance']['value']) / Decimal(1000)  # Convert to kilometers
                                total_distance += distance * round_trips_per_year

        # Calculate total transportation cost based on the distance and fuel price
        total_transportation_cost = total_distance * fuel_consumption_rate * current_fuel_price
        total_effective_cost = property.price + total_transportation_cost

        # Render the result on the same page
        context = {
            'property': property,
            'vehicles': vehicles,
            'total_distance': total_distance,
            'total_transportation_cost': total_transportation_cost,
            'total_effective_cost': total_effective_cost,
            'work_location': work_location,
            'work_trips_per_week': work_trips_per_week,
            'other_locations': other_locations,
            'current_fuel_price': current_fuel_price,
        }
        return render(request, 'cost_estimation_detail.html', context)

    context = {
        'property': property,
        'vehicles': vehicles,
    }
    return render(request, 'cost_estimation_detail.html', context)
'''






