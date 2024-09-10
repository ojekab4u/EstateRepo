from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Property, PropertyImage, MultipleFileInput, User

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'is_agent')

class AgentRegistrationForm(UserRegistrationForm):
    is_agent = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput())

class GeneralUserRegistrationForm(UserRegistrationForm):
    is_agent = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput())

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['title', 'description', 'address', 'city', 'state', 'zip_code', 'price', 'property_type', 'bedrooms', 'bathrooms','square_feet','main_image','sale_or_rent']
        

class PropertyImageForm(forms.ModelForm):
    image = forms.ImageField(widget=MultipleFileInput)

    class Meta:
        model = PropertyImage
        fields = ['image']
# class PropertyImageForm(forms.ModelForm):
#     image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

#     class Meta:
#         model = PropertyImage
#         fields = ['image']


class PropertySearchForm(forms.Form):
    search_query = forms.CharField(label='Search', max_length=100)
    address = forms.CharField(label='Address', max_length=255, required=False)
    min_price = forms.DecimalField(label='Min Price', required=False)
    max_price = forms.DecimalField(label='Max Price', required=False)
    # More  for other parameters may be added

from .models import Property, Vehicle

class CostEstimationForm(forms.Form):
    property_id = forms.ModelChoiceField(queryset=Property.objects.all(), widget=forms.HiddenInput())
    house_rent = forms.DecimalField(max_digits=10, decimal_places=2)
    work_location = forms.CharField(max_length=255)
    other_locations = forms.CharField(max_length=255, required=False)
    vehicle = forms.ModelChoiceField(queryset=Vehicle.objects.none())
    current_fuel_price = forms.DecimalField(max_digits=5, decimal_places=2)
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(user=user)

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['name', 'fuel_consumption_rate']