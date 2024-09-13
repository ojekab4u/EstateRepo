@login_required
def cost_estimation_detail(request, property_id):
    property = get_object_or_404(Property, pk=property_id)
    google_api_key = settings.GOOGLE_API_KEY
    user = request.user
    vehicles = Vehicle.objects.filter(user=user)    

    # Geocode the property address to get lat/lng
    property_address = f"{property.address}, {property.city}, {property.state}, {property.zip_code}"
    property_lat_lng = get_geocode(property_address, google_api_key)

    # house_lat = property_lat_lng['lat']
    # house_lng = property_lat_lng['lng']

    # Initialize variables to avoid UnboundLocalError
    work_location = None
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

            vehicle_summaries.append({
                'name': vehicle.name,
                'work_location': car['work_location'],
                'work_trips_per_week': work_trips_per_week,
                'other_locations': ', '.join([f"{loc['name']}: {loc['trips_per_week']}" for loc in car['other_locations']]),
                'total_distance': total_distance_to_work_and_other_loc,
                'transportation_cost': transportation_cost
            })

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