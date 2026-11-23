
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
from . import engine
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
    data = request.POST.copy()
    _apply_fuel_unit(data)
    form = VehicleForm(data or None)
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
    data = request.POST.copy()
    _apply_fuel_unit(data)
    form = VehicleForm(data or None, instance=vehicle)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vehicle updated.')
        return redirect('vehicle_list')
    return render(request, 'vehicle_form.html', {'form': form, 'editing': True, 'vehicle': vehicle})


def _apply_fuel_unit(data):
    """Users think in km/L ("my car does 12"); we store litres/km."""
    if data.get('fuel_unit') == 'kmpl':
        try:
            kmpl = float(data.get('fuel_consumption_rate') or 0)
            data['fuel_consumption_rate'] = str(round(1 / kmpl, 6)) if kmpl else ''
        except (TypeError, ValueError, ZeroDivisionError):
            data['fuel_consumption_rate'] = ''


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
from .models import Property, Vehicle, HistoricalData, FuelPrice, EstimateProfile, ProfileTrip, ProfilePlace
from .utils import get_place_id, get_route_distance_from_place_ids

logger = logging.getLogger(__name__)


@login_required
def cost_estimation_detail(request, property_id):
    """Personal estimate: the user's saved trips applied to one property."""
    property = get_object_or_404(Property, pk=property_id)
    user = request.user

    if user.is_agent:
        messages.info(request, "Estimation is for house-hunters — agents manage listings.")
        return redirect('index')

    profile = EstimateProfile.for_user(user)
    trips = (ProfileTrip.objects.filter(user=user)
             .select_related('place', 'vehicle'))

    if request.method == 'POST':
        raw_fuel = request.POST.get('fuel_price') or ''
        try:
            fuel_price = Decimal(raw_fuel) if raw_fuel else None
        except InvalidOperation:
            messages.error(request, "Fuel price must be a number.")
            return redirect('cost_estimation_detail', property.pk)

        if fuel_price is None:
            fuel_price = profile.fuel_price or FuelPrice.latest('petrol')
        if fuel_price is None:
            messages.error(request, "No fuel price available — enter one to estimate.")
            return redirect('cost_estimation_detail', property.pk)

        if not trips.exists():
            messages.info(request, "Add at least one regular trip to your profile first.")
            return redirect('commute_profile')

        result = engine.estimate_for_property(user, property, fuel_price)

        rent_yearly = property.price if isinstance(property.price, Decimal) else Decimal(str(property.price))
        rent_monthly = rent_yearly / 12
        rent_weekly = rent_yearly / 52
        total_transport = result['total_transport']
        effective_yearly = rent_yearly + total_transport

        # Snapshot — editing the profile later never changes this saved number
        snapshot = {
            'fuel_price': str(fuel_price),
            'geo_provider': settings.GEO_PROVIDER,
            'trips': [
                {k: (str(v) if isinstance(v, Decimal) else v)
                 for k, v in trip.items()} for trip in result['trips']
            ],
        }
        vehicle_names = sorted({t['vehicle'] for t in result['trips'] if not t.get('skipped')})
        HistoricalData.objects.create(
            user=user,
            property=property,
            vehicle_name=(vehicle_names[0] if len(vehicle_names) == 1
                          else f"Household ({len(vehicle_names)} vehicles)"),
            work_location=f"{len(result['trips'])} regular trips",
            work_trips_per_week=sum(
                t['trips_per_week'] for t in result['trips'] if not t.get('skipped')),
            other_locations=json.dumps(snapshot),
            total_distance=sum(
                (t['annual_km'] for t in result['trips'] if not t.get('skipped')),
                Decimal('0')),
            transportation_cost=total_transport,
            total_effective_cost=effective_yearly,
        )

        context = {
            'property': property,
            'result': result,
            'fuel_price': fuel_price,
            'trips': trips,
            'rent_yearly': rent_yearly,
            'rent_monthly': rent_monthly,
            'rent_weekly': rent_weekly,
            'total_transport': total_transport,
            'effective_yearly': effective_yearly,
            'effective_monthly': effective_yearly / 12,
            'effective_weekly': effective_yearly / 52,
            'total_transport_monthly': total_transport / 12,
            'total_transport_weekly': total_transport / 52,
        }
        return render(request, 'cost_estimation_detail.html', context)

    # GET
    default_fuel = profile.fuel_price or FuelPrice.latest('petrol') or ""
    context = {
        'property': property,
        'trips': trips,
        'vehicle_count': Vehicle.objects.filter(user=user).count(),
        'default_fuel_price': default_fuel,
        'has_trips': trips.exists(),
    }
    return render(request, 'cost_estimation_detail.html', context)


@login_required
def trip_list(request):
    """Profile hub: the user's regular trips (place, vehicle, frequency)."""
    profile = EstimateProfile.for_user(request.user)

    # One-time migration: turn the old profile fields into a real trip
    if (not ProfileTrip.objects.filter(user=request.user).exists()
            and profile.work_location):
        vehicle = Vehicle.objects.filter(user=request.user).first()
        if vehicle:
            place, _ = ProfilePlace.objects.get_or_create(
                user=request.user, label='Work',
                defaults={'address': profile.work_location})
            ProfileTrip.objects.create(
                user=request.user, place=place, vehicle=vehicle,
                return_trips_per_week=profile.work_trips_per_week or 10)
            messages.info(request, 'Your saved work route is now a regular trip.')

    if request.method == 'POST' and request.POST.get('action') == 'fuel':
        raw = request.POST.get('fuel_price') or ''
        try:
            profile.fuel_price = Decimal(raw) if raw else None
        except InvalidOperation:
            messages.error(request, 'Fuel price must be a number.')
            return redirect('commute_profile')
        profile.save()
        messages.success(request, 'Fuel price saved.')
        return redirect('commute_profile')

    trips = (ProfileTrip.objects.filter(user=request.user)
             .select_related('place', 'vehicle'))
    context = {
        'trips': trips,
        'vehicle_count': Vehicle.objects.filter(user=request.user).count(),
        'profile': profile,
        'latest_petrol': FuelPrice.latest('petrol'),
    }
    return render(request, 'commute_profile.html', context)


@login_required
def trip_add(request):
    if request.method == 'POST':
        label = (request.POST.get('label') or '').strip() or 'Place'
        address = (request.POST.get('address') or '').strip()
        trips_per_week = request.POST.get('return_trips_per_week') or '1'
        vehicle_id = request.POST.get('vehicle')
        if not address:
            messages.error(request, 'An address is required.')
            return redirect('trip_add')
        try:
            trips_per_week = int(trips_per_week)
        except ValueError:
            messages.error(request, 'Trips per week must be a whole number.')
            return redirect('trip_add')
        vehicle = Vehicle.objects.filter(user=request.user, pk=vehicle_id).first()
        if not vehicle:
            messages.error(request, 'Pick one of your vehicles (add one first if needed).')
            return redirect('trip_add')

        place, _ = ProfilePlace.objects.get_or_create(
            user=request.user, label=label,
            defaults={'address': address})
        if place.address != address:
            place.address = address
        if place.coords() is None:
            g = geo.geocode(address)
            if g:
                place.latitude, place.longitude = g['lat'], g['lng']
        place.save()
        ProfileTrip.objects.create(
            user=request.user, place=place, vehicle=vehicle,
            return_trips_per_week=trips_per_week)
        messages.success(request, f'Trip saved: {label}.')
        return redirect('commute_profile')

    context = {
        'vehicles': Vehicle.objects.filter(user=request.user),
        'places': ProfilePlace.objects.filter(user=request.user),
    }
    return render(request, 'trip_form.html', {'editing': False})


@login_required
def trip_edit(request, pk):
    trip = get_object_or_404(ProfileTrip, pk=pk)
    if trip.user != request.user:
        raise Http404('Trip not found')
    if request.method == 'POST':
        label = (request.POST.get('label') or '').strip() or trip.place.label
        address = (request.POST.get('address') or '').strip()
        vehicle_id = request.POST.get('vehicle')
        try:
            trip.return_trips_per_week = int(request.POST.get('return_trips_per_week') or 1)
        except ValueError:
            trip.return_trips_per_week = 1
        vehicle = Vehicle.objects.filter(user=request.user, pk=vehicle_id).first()
        if not vehicle:
            messages.error(request, 'Pick one of your vehicles.')
            return redirect('trip_edit', pk)
        if address and address != trip.place.address:
            trip.place.address = address
            g = geo.geocode(address)
            trip.place.latitude = g['lat'] if g else None
            trip.place.longitude = g['lng'] if g else None
        trip.place.label = label
        trip.place.save()
        trip.vehicle = vehicle
        trip.save()
        messages.success(request, 'Trip updated.')
        return redirect('commute_profile')

    context = {
        'trip': trip,
        'editing': True,
        'vehicles': Vehicle.objects.filter(user=request.user),
    }
    return render(request, 'trip_form.html', context)


@login_required
def trip_delete(request, pk):
    trip = get_object_or_404(ProfileTrip, pk=pk)
    if trip.user != request.user:
        raise Http404('Trip not found')
    if request.method == 'POST':
        label = trip.place.label
        trip.delete()
        if not ProfileTrip.objects.filter(place=trip.place).exists():
            trip.place.delete()
        messages.success(request, f'Trip removed: {label}.')
        return redirect('commute_profile')
    return render(request, 'trip_delete_confirm.html', {'trip': trip})
