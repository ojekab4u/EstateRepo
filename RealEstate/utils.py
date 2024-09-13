# import requests
# from django.conf import settings

# # def get_distance_matrix(origin, destination):
# #     api_key = settings.GOOGLE_MAPS_API_KEY
# #     endpoint = 'https://maps.googleapis.com/maps/api/distancematrix/json?'
# #     params = {
# #         'origins': origin,
# #         'destinations': destination,
# #         'key': api_key
# #     }
# #     response = requests.get(endpoint, params=params)
# #     if response.status_code != 200:
# #         return None
# #     distance_matrix = response.json()
# #     if distance_matrix['status'] != 'OK':
# #         return None
# #     return distance_matrix




# # def get_distance_matrix(origin, destination, api_key):
# #     url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
# #     params = {
# #         'origins': origin,
# #         'destinations': destination,
# #         'key': api_key
# #     }
# #     response = requests.get(url, params=params)
# #     if response.status_code == 200:
# #         data = response.json()
# #         if data.get('status') != 'OK':
# #             print("API Error:", data.get('status'))
# #             return None  # or return some default value
# #         return data
# #     return None

# import requests
# from django.conf import settings
# from django.core.exceptions import ValidationError

# # def get_distance_matrix(origin, destination, api_key):
# #     url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
# #     params = {
# #         'origins': origin,
# #         'destinations': destination,
# #         'key': api_key
# #     }
    
# #     try:
# #         response = requests.get(url, params=params)
# #         response.raise_for_status()  # Raise an HTTPError for bad responses
# #         data = response.json()
        
# #         # Check if the API returned an error status
# #         if data.get('status') != 'OK':
# #             print(f"API Error: {data.get('status')}")
# #             return None
        
# #         return data
    
# #     except requests.exceptions.RequestException as e:
# #         print(f"Request failed: {e}")
# #         return None

# import requests
# from django.conf import settings

# def get_distance_matrix(origin, destination, api_key):
#     # Set the mode to driving explicitly
#     mode = "driving"
    
#     # Build the request URL
#     request_url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&mode={mode}&key={api_key}"
    
#     # Print the request URL to debug
#     print(f"Request URL: {request_url}")
    
#     try:
#         # Make the API request
#         response = requests.get(request_url)
        
#         # Print the response JSON to debug
#         print("Response Data:", response.json())
        
#         # Check if the request was successful
#         if response.status_code == 200:
#             return response.json()
#         else:
#             print(f"API Error: {response.status_code} - {response.text}")
#             return None
#     except requests.exceptions.RequestException as e:
#         print(f"Request failed: {e}")
#         return None


import requests
from django.conf import settings




def get_geocode(address, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url)
    result = response.json()
    if result['status'] == 'OK':
        location = result['results'][0]['geometry']['location']
        return {
            'lat': location['lat'],
            'lng': location['lng']
        }
    return None
def get_distance_matrix(origin_coords, destination_coords, api_key):
    origin = f"{origin_coords[0]},{origin_coords[1]}"
    destination = f"{destination_coords[0]},{destination_coords[1]}"
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&mode=driving&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None
def get_distance_matrix_with_place_id(origin_place_id, destination_place_id, api_key):
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins=place_id:{origin_place_id}&destinations=place_id:{destination_place_id}&key={api_key}"
    response = requests.get(url)
    return response.json()


# Function to calculate route distance using the Google Maps Routes API
def get_route_distance(origin, destination, api_key):
    """
    Use the Google Maps Routes API to calculate the distance between two locations.
    """
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin[0]},{origin[1]}",  # Latitude,Longitude format
        "destination": f"{destination[0]},{destination[1]}",
        "key": api_key,
        "mode": "driving",  # You can choose driving, walking, bicycling, etc.
        "units": "metric",  # Return results in kilometers
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            route = data['routes'][0]
            leg = route['legs'][0]
            distance_in_meters = leg['distance']['value']  # Distance in meters
            return distance_in_meters / 1000  # Convert to kilometers
        else:
            print(f"Error in response: {data['status']}")
            return None
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None


# Function to get Place ID using the Google Places API
def get_place_id(address, api_key):
    base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": address,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": api_key,
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK' and data.get('candidates'):
            return data['candidates'][0]['place_id']
        else:
            print(f"Error in place search response: {data['status']}")
            return None
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None

# Function to calculate route distance using the Google Maps Routes API
def get_route_distance_from_place_ids(origin_place_id, destination_place_id, api_key):
    """
    Use the Google Maps Routes API to calculate the distance between two locations using Place IDs.
    """
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"place_id:{origin_place_id}",
        "destination": f"place_id:{destination_place_id}",
        "key": api_key,
        "mode": "driving",
        "units": "metric",
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            route = data['routes'][0]
            leg = route['legs'][0]
            distance_in_meters = leg['distance']['value']  # Distance in meters
            
            print(f"Distance in meter: {distance_in_meters}")
            return distance_in_meters / 1000  # Convert to kilometers
        else:
            print(f"Error in response: {data['status']}")
            return None
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None
