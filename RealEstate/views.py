
from django.conf import settings
# from .utils import get_distance
from django.contrib.messages import success, error
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse, HttpResponseRedirect, Http404
from .models import Property, PropertyImage, Property, Vehicle
from decimal import Decimal, ROUND_HALF_UP
from .forms import (UserRegistrationForm,
                    PropertyForm, PropertyEditForm,
                    PropertySearchForm,
                    PropertyImageForm,
                    VehicleForm
                    )
from .forms import AgentRegistrationForm, GeneralUserRegistrationForm
from django.urls import reverse_lazy

from django.contrib import messages
from .models import Property, UserLocation, Vehicle
from . import geo
from .utils import( get_distance_matrix,
                   get_distance_matrix_with_place_id,
                   get_geocode,
                   get_route_distance,
                   get_route_distance_from_place_ids,
                   get_place_id
                   )

from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, F
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
    featured = (Property.objects
                .order_by(F('true_cost_yearly').asc(nulls_last=True))
                .prefetch_related('images'))[:3]
    context = {
        'featured': featured,
        'listing_count': Property.objects.count(),
        'estimate_runs': HistoricalData.objects.count(),
        'petrol': FuelPrice.latest('petrol'),
        'diesel': FuelPrice.latest('diesel'),
    }
    return render(request, 'home.html', context)

def about(request):
    if request.method == "POST":
        pass    
    return render(request, 'legacy_theme/about.html')

def service(request):
    if request.method == "POST":
        pass
    return render(request, 'legacy_theme/services.html')


def contact(request):
    if request.method == "POST":
        # Handle form submission logic here
        pass
    return render(request, 'legacy_theme/contact.html')

def blog(request):
    if request.method == "POST":
        # Handle form submission logic here
        pass
    # posts = BlogPost.objects.all()
    # return render(request, 'blog.html', {'posts': posts})
    return render(request, 'legacy_theme/blog.html')

def property_list(request):
    sale_or_rent = request.GET.get('sale_or_rent', 'rent') or 'rent'
    properties = Property.objects.filter(sale_or_rent=sale_or_rent)
    query = request.GET.get('q') or ''
    price_min = request.GET.get('price_min') or ''
    price_max = request.GET.get('price_max') or ''
    bedrooms = request.GET.get('bedrooms') or ''
    bathrooms = request.GET.get('bathrooms') or ''
    property_type = request.GET.get('property_type') or ''
    max_true_cost = request.GET.get('max_true_cost') or ''

    # Never let junk input (e.g. "None", "abc") become a DB filter — degrade
    # gracefully by ignoring the parameter instead of 500-ing.
    def _clean_number(value):
        try:
            Decimal(str(value))
            return value
        except (InvalidOperation, TypeError, ValueError):
            return ''

    if query:
        properties = properties.filter(
            Q(title__icontains=query) | Q(city__icontains=query) | Q(address__icontains=query))
    if _clean_number(price_min):
        properties = properties.filter(price__gte=price_min)
    if _clean_number(price_max):
        properties = properties.filter(price__lte=price_max)
    if bedrooms and bedrooms.isdigit():
        properties = properties.filter(bedrooms__gte=bedrooms)   # "2+" semantics
    if bathrooms and bathrooms.isdigit():
        properties = properties.filter(bathrooms__gte=bathrooms)
    if property_type in ('Apartment', 'House', 'Condo'):
        properties = properties.filter(property_type=property_type)
    if _clean_number(max_true_cost):
        properties = properties.filter(true_cost_yearly__lte=max_true_cost)

    # Sorting — true-cost sort is the product's signature (DB-cached, no API)
    sort = request.GET.get('sort') or ''
    if sort == 'price':
        properties = properties.order_by('price')
    elif sort == 'newest':
        properties = properties.order_by('-created_at')
    else:  # default: lowest true cost
        sort = 'true_cost'
        properties = properties.order_by(F('true_cost_yearly').asc(nulls_last=True))

    from django.core.paginator import Paginator
    paginator = Paginator(properties, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Querystring for pagination/sort links that preserves active filters
    params = request.GET.copy()
    params.pop('page', None)
    base_querystring = params.urlencode()

    context = {
        'page_obj': page_obj,
        'properties': page_obj.object_list,
        'total_count': paginator.count,
        'query': query,
        'price_min': price_min,
        'price_max': price_max,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'property_type': property_type,
        'max_true_cost': max_true_cost,
        'sale_or_rent': sale_or_rent,
        'sort': sort,
        'base_querystring': base_querystring,
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

    context = {
        'property': property,
        'place_type': place_type,
        'images': images,
        'property_lat': property.latitude,
        'property_lng': property.longitude,
        'property_address_full': f"{property.address}, {property.city}, {property.state}, {property.zip_code}",
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
            # Geocode ONCE at listing creation (cached in geo.py, ~1s); store
            # coords so maps and the estimator never re-geocode. Best-effort:
            # a failed geocode leaves coords null and the map falls back.
            _coords = geo.geocode(
                f"{property.address}, {property.city}, {property.state}, {property.zip_code}")
            if _coords:
                property.latitude, property.longitude = _coords['lat'], _coords['lng']
            property.save()

            for image in images:
                PropertyImage.objects.create(property=property, image=image)

            property.compute_true_cost()
            messages.success(request, 'Property created successfully!')
            return redirect('agent_dashboard')
    else:
        property_form = PropertyForm()

    return render(request, 'property_form.html', {
        'form': property_form, 'google_api_key': settings.GOOGLE_API_KEY,
    })
    
   
  
    
    
@login_required
def add_vehicle(request):
    form = VehicleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        vehicle = form.save(commit=False)
        vehicle.user = request.user
        vehicle.save()
        messages.success(request, 'Vehicle added.')
        return redirect('vehicle_list')
    return render(request, 'vehicle_form.html', {'form': form, 'editing': False})


@login_required
def edit_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if vehicle.user != request.user:
        raise Http404("Vehicle not found")
    form = VehicleForm(request.POST or None, instance=vehicle)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vehicle updated.')
        return redirect('vehicle_list')
    return render(request, 'vehicle_form.html', {'form': form, 'editing': True, 'vehicle': vehicle})


@login_required
def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if vehicle.user != request.user:
        raise Http404("Vehicle not found")
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle removed.')
        return redirect('vehicle_list')
    used_in = HistoricalData.objects.filter(user=request.user, vehicle_name=vehicle.name).count()
    return render(request, 'vehicle_delete_confirm.html', {'vehicle': vehicle, 'used_in': used_in})

@login_required
def vehicle_list(request):
    vehicles = Vehicle.objects.filter(user=request.user)
    return render(request, 'vehicle_list.html', {'vehicles': vehicles})


# ---------------------------------------------------------------------------
# Role-based endpoints: agent workspace & customer saved estimates
# ---------------------------------------------------------------------------

def agent_required_redirect(user):
    """Pass for logged-in agents only (covers unauthenticated users too)."""
    return user.is_authenticated and user.is_agent


@user_passes_test(agent_required_redirect, login_url='login')
def agent_dashboard(request):
    """Agent workspace: their listings + how many estimate runs their
    properties have received. (Metrics shown are real queries — no fake
    numbers until view tracking exists.)"""
    listings = (
        Property.objects.filter(owner=request.user)
        .prefetch_related('images')
        .order_by('-created_at')
    )
    estimate_runs = HistoricalData.objects.filter(property__owner=request.user).count()
    context = {
        'listings': listings,
        'listing_count': listings.count(),
        'estimate_runs': estimate_runs,
    }
    return render(request, 'agent_dashboard.html', context)


@login_required
def property_edit(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    if prop.owner != request.user:
        raise Http404("Listing not found")  # don't reveal other agents' listings
    if not request.user.is_agent:
        messages.info(request, "Only agents can edit listings.")
        return redirect('index')

    if request.method == 'POST':
        form = PropertyEditForm(request.POST, request.FILES, instance=prop)
        images = request.FILES.getlist('additional_images')
        if form.is_valid():
            new_image = form.cleaned_data.get('main_image')
            if new_image:
                prop.main_image = new_image
            form.save()
            for image in images:
                PropertyImage.objects.create(property=prop, image=image)
            prop.compute_true_cost()  # price may have changed
            messages.success(request, 'Listing updated.')
            return redirect('agent_dashboard')
    else:
        form = PropertyEditForm(instance=prop)
    return render(request, 'property_edit.html', {'form': form, 'property': prop})


@login_required
def property_delete(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    if prop.owner != request.user:
        raise Http404("Listing not found")
    if not request.user.is_agent:
        messages.info(request, "Only agents can delete listings.")
        return redirect('index')

    if request.method == 'POST':
        prop.delete()
        messages.success(request, 'Listing deleted.')
        return redirect('agent_dashboard')
    return render(request, 'property_delete_confirm.html', {'property': prop})


@login_required
def my_estimates(request):
    """Customer saved estimates — reads the HistoricalData rows now persisted
    by the cost estimator."""
    estimates = (
        HistoricalData.objects.filter(user=request.user)
        .select_related('property')
        .order_by('-date_field')
    )
    # Aggregate view: cheapest true cost among the user's estimates
    cheapest = estimates.order_by('total_effective_cost').first()
    context = {
        'estimates': estimates,
        'cheapest': cheapest,
    }
    return render(request, 'my_estimates.html', context)


@login_required
def commute_profile(request):
    """The user's saved commute identity — powers one-tap estimates.
    True cost is personal: vehicles (added separately), destinations,
    trips and fuel price live here."""
    profile = EstimateProfile.for_user(request.user)

    if request.method == 'POST':
        fuel = request.POST.get('fuel_price') or ''
        profile.work_location = (request.POST.get('work_location') or '').strip()
        trips = request.POST.get('work_trips_per_week') or ''
        try:
            profile.fuel_price = Decimal(fuel) if fuel else None
        except InvalidOperation:
            messages.error(request, "Fuel price must be a number.")
            return redirect('commute_profile')
        try:
            profile.work_trips_per_week = int(trips) if trips else None
        except ValueError:
            messages.error(request, "Trips per week must be a whole number.")
            return redirect('commute_profile')
        profile.save()
        messages.success(request, 'Profile saved — estimates are now one tap.')
        return redirect('commute_profile')

    if not profile.fuel_price:
        latest = FuelPrice.latest('petrol')
        if latest is not None:
            profile.fuel_price = latest

    context = {
        'profile': profile,
        'vehicle_count': Vehicle.objects.filter(user=request.user).count(),
        'latest_petrol': FuelPrice.latest('petrol'),
    }
    return render(request, 'commute_profile.html', context)


import json
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from decimal import Decimal, InvalidOperation
from .models import Property, Vehicle, HistoricalData, FuelPrice, EstimateProfile
from .utils import get_place_id, get_route_distance_from_place_ids

logger = logging.getLogger(__name__)

@login_required
def cost_estimation_detail(request, property_id):
    property = get_object_or_404(Property, pk=property_id)
    google_api_key = settings.GOOGLE_API_KEY
    user = request.user
    vehicles = Vehicle.objects.filter(user=user)    
    
    # Geocode the property address to get lat/lng (cached; free OSM provider by default).
    # Properties with stored coords skip geocoding entirely.
    property_address = f"{property.address}, {property.city}, {property.state}, {property.zip_code}"
    if property.latitude is not None and property.longitude is not None:
        property_lat_lng = {"lat": property.latitude, "lng": property.longitude, "display": ""}
    else:
        property_lat_lng = geo.geocode(property_address)

    if request.user.is_agent:
        messages.info(request, "Agents are not allowed to use estimator")
        return redirect('index')  # Redirect agents to a different page as per your logic

    house_lat = property_lat_lng['lat'] if property_lat_lng else None
    house_lng = property_lat_lng['lng'] if property_lat_lng else None

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
        if not current_fuel_price:
            # Personal profile first, then the admin-managed national price
            _profile = EstimateProfile.for_user(user)
            latest = _profile.fuel_price or FuelPrice.latest('petrol')
            current_fuel_price = str(latest) if latest is not None else "0"
        try:
            current_fuel_price = Decimal(current_fuel_price)
        except InvalidOperation:
            return HttpResponse("Invalid fuel price. Please enter a valid number.")

        # Initialize total distance for all vehicles
        total_distance_all_vehicles_yearly = Decimal(0)
        # Initialize individual vehicle distance mapping
        vehicle_distances = {}
        vehicle_summaries = []
        total_transportation_cost = Decimal(0)

        # Rent is fixed for the whole estimate — compute once before the vehicle loop
        rent_weekly = property.price / 52
        rent_monthly = property.price / 12
        rent_yearly = property.price

        # Iterate over each car's details
        for car in car_details:
            vehicle = get_object_or_404(Vehicle, pk=car['vehicle_id'])
            fuel_consumption_rate = Decimal(vehicle.fuel_consumption_rate)
            work_trips_per_week = car['work_trips_per_week']
            work_round_trips_per_year = work_trips_per_week * 52  # Multiply by 52 for yearly calculation

            property_coords = (house_lat, house_lng) if house_lat is not None else None
            work_coords = geo.geocode(car['work_location'])
            work_coords = (work_coords['lat'], work_coords['lng']) if work_coords else None

            total_distance_for_vehicle = Decimal(0)


            # Calculate round-trip distance for work location
            work_distance_one_way = geo.route_distance_km(property_coords, work_coords)
            work_distance_in_kilometers = Decimal(str(work_distance_one_way)) * 2 if work_distance_one_way else Decimal(0)
            total_work_distance = work_distance_in_kilometers * Decimal(work_round_trips_per_year)
            total_distance_for_vehicle += total_work_distance

            # Calculate round-trip distance for other locations
            for location in car['other_locations']:
                loc_coords = geo.geocode(location['address'])
                loc_coords = (loc_coords['lat'], loc_coords['lng']) if loc_coords else None
                distance_one_way = geo.route_distance_km(property_coords, loc_coords)
                distance_in_kilometers = Decimal(str(distance_one_way)) * 2 if distance_one_way else Decimal(0)
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

            # Persist the estimate (activates the dormant HistoricalData model —
            # previously results were never saved anywhere)
            profile = {
                'fuel_price': str(current_fuel_price),
                'work_trips_per_week': car['work_trips_per_week'],
                'other_locations': car['other_locations'],
                'geo_provider': settings.GEO_PROVIDER,
            }
            HistoricalData.objects.create(
                user=user,
                property=property,
                vehicle_name=vehicle.name,
                work_location=car['work_location'],
                work_trips_per_week=car['work_trips_per_week'],
                other_locations=json.dumps(profile),
                total_distance=total_distance_for_vehicle,
                transportation_cost=vehicle_summary['yearly_estimate'],
                total_effective_cost=rent_yearly + vehicle_summary['yearly_estimate'],
            )

        # Rent already computed above (rent_weekly / rent_monthly / rent_yearly)

        
        
        
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
    profile = EstimateProfile.for_user(user)
    context = {
        'property': property,
        'vehicles': vehicles,
        'house_lat': house_lat,
        'house_lng': house_lng,
        'google_api_key': settings.GOOGLE_API_KEY,
        'default_fuel_price': profile.fuel_price or FuelPrice.latest('petrol') or "",
        'profile_work_location': profile.work_location,
        'profile_trips': profile.work_trips_per_week or 10,
        'has_profile': bool(profile.work_location or profile.work_trips_per_week),
    }

    return render(request, 'cost_estimation_detail.html', context)







