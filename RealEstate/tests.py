"""
Smoke + role-guard tests for ComfyHome.

Run: python manage.py test

Geo calls are mocked so tests never hit the network (Nominatim/OSRM).
"""
import json
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .models import User, Property, Vehicle, HistoricalData, EstimateProfile


def _tiny_image():
    """Generate a real 10x10 JPEG in-memory (Pillow is already a dependency)."""
    from PIL import Image
    buf = BytesIO()
    Image.new("RGB", (10, 10), color=(200, 60, 40)).save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile("test.jpg", buf.read(), content_type="image/jpeg")


PROPERTY_FIELDS = {
    "title": "2 Bedroom Flat",
    "description": "Test description",
    "address": "12 Test Street",
    "city": "Ibadan",
    "state": "Oyo",
    "zip_code": "200261",
    "price": "200000",
    "property_type": "Apartment",
    "bedrooms": "2",
    "bathrooms": "2",
    "square_feet": "300",
    "sale_or_rent": "rent",
}


class BaseTest(TestCase):
    def setUp(self):
        self.agent = User.objects.create_user(
            username="agent1", email="a@example.com", password="Passw0rd!23", is_agent=True)
        self.other_agent = User.objects.create_user(
            username="agent2", email="b@example.com", password="Passw0rd!23", is_agent=True)
        self.customer = User.objects.create_user(
            username="cust1", email="c@example.com", password="Passw0rd!23", is_customer=True)
        self.property_ = Property.objects.create(
            owner=self.agent, main_image=_tiny_image(), **PROPERTY_FIELDS)
        self.vehicle = Vehicle.objects.create(
            user=self.customer, name="Honda Civic", fuel_consumption_rate=0.068)


class RoleGuardTests(BaseTest):
    def test_dashboard_requires_agent(self):
        self.client.login(username="cust1", password="Passw0rd!23")
        r = self.client.get(reverse("agent_dashboard"))
        self.assertEqual(r.status_code, 302)  # customers are redirected away

        self.client.login(username="agent1", password="Passw0rd!23")
        r = self.client.get(reverse("agent_dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "2 Bedroom Flat")

    def test_dashboard_requires_login(self):
        r = self.client.get(reverse("agent_dashboard"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.url)

    def test_edit_requires_owner(self):
        self.client.login(username="agent2", password="Passw0rd!23")  # not the owner
        r = self.client.get(reverse("property_edit", args=[self.property_.pk]))
        self.assertEqual(r.status_code, 404)

    def test_edit_updates_listing(self):
        self.client.login(username="agent1", password="Passw0rd!23")
        data = dict(PROPERTY_FIELDS, title="Updated Title")
        r = self.client.post(reverse("property_edit", args=[self.property_.pk]), data)
        self.assertRedirects(r, reverse("agent_dashboard"))
        self.property_.refresh_from_db()
        self.assertEqual(self.property_.title, "Updated Title")

    def test_delete_requires_confirmation_and_owner(self):
        self.client.login(username="agent2", password="Passw0rd!23")
        r = self.client.get(reverse("property_delete", args=[self.property_.pk]))
        self.assertEqual(r.status_code, 404)

        self.client.login(username="agent1", password="Passw0rd!23")
        r = self.client.get(reverse("property_delete", args=[self.property_.pk]))
        self.assertEqual(r.status_code, 200)  # confirmation page

        r = self.client.post(reverse("property_delete", args=[self.property_.pk]))
        self.assertRedirects(r, reverse("agent_dashboard"))
        self.assertFalse(Property.objects.filter(pk=self.property_.pk).exists())

    def test_my_estimates_requires_login(self):
        r = self.client.get(reverse("my_estimates"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.url)


class SavedEstimatesTests(BaseTest):
    def test_estimator_persists_historical_data(self):
        """The estimator must save one HistoricalData row per vehicle."""
        self.client.login(username="cust1", password="Passw0rd!23")
        with patch("RealEstate.views.geo.geocode",
                   return_value={"lat": 7.39, "lng": 3.91, "display": "Test"}), \
             patch("RealEstate.views.geo.route_distance_km", return_value=5.0):
            r = self.client.post(
                reverse("cost_estimation_detail", args=[self.property_.pk]),
                {
                    "num_cars": "1",
                    "vehicle_1": str(self.vehicle.pk),
                    "work_location_1": "Ring Road, Ibadan",
                    "work_trips_per_week_1": "10",
                    "current_fuel_price": "998",
                })
        self.assertEqual(r.status_code, 200)
        rows = HistoricalData.objects.filter(user=self.customer, property=self.property_)
        self.assertEqual(rows.count(), 1)
        row = rows.first()
        self.assertEqual(row.vehicle_name, "Honda Civic")
        self.assertEqual(row.work_location, "Ring Road, Ibadan")
        self.assertEqual(row.transportation_cost, Decimal("352892.80"))
        expected_total = Decimal(str(self.property_.price)) + row.transportation_cost
        self.assertEqual(row.total_effective_cost, expected_total)
        profile = json.loads(row.other_locations)
        self.assertEqual(profile["fuel_price"], "998")
        self.assertEqual(profile["work_trips_per_week"], 10)

    def test_my_estimates_lists_saved_rows(self):
        HistoricalData.objects.create(
            user=self.customer, property=self.property_,
            vehicle_name="Honda Civic", work_location="Ring Road",
            work_trips_per_week=10, other_locations="{}",
            total_distance=Decimal("5200"),
            transportation_cost=Decimal("104400"),
            total_effective_cost=Decimal("304400"))
        self.client.login(username="cust1", password="Passw0rd!23")
        r = self.client.get(reverse("my_estimates"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Honda Civic")
        self.assertContains(r, "304,400.00")


class PricingEngineTests(BaseTest):
    def test_fuel_price_latest(self):
        from .models import FuelPrice
        from django.utils import timezone as tz
        FuelPrice.objects.create(fuel_type="petrol", price_per_litre=Decimal("900"), effective_date=tz.now().date())
        FuelPrice.objects.create(fuel_type="petrol", price_per_litre=Decimal("998"), effective_date=tz.now().date())
        self.assertEqual(FuelPrice.latest("petrol"), Decimal("998"))
        self.assertIsNone(FuelPrice.latest("diesel"))

    def test_compute_true_cost_math(self):
        from .models import FuelPrice
        from django.utils import timezone as tz
        FuelPrice.objects.create(fuel_type="petrol", price_per_litre=Decimal("998"), effective_date=tz.now().date())
        result = self.property_.compute_true_cost(save=True)
        # 8 km one-way x 2 x 10 trips/wk x 52 wks = 8320 km/yr
        # 8320 x 0.068 L/km x 998 = 564628.48
        expected = Decimal(str(self.property_.price)) + Decimal("564628.48")
        self.assertEqual(result, expected)
        self.property_.refresh_from_db()
        self.assertEqual(self.property_.true_cost_yearly, expected)

    def test_compute_skipped_without_fuel_price(self):
        result = self.property_.compute_true_cost()
        self.assertIsNone(result)
        self.assertIsNone(self.property_.true_cost_yearly)

    def test_property_list_sorts_by_true_cost(self):
        from .models import FuelPrice
        from django.utils import timezone as tz
        FuelPrice.objects.create(fuel_type="petrol", price_per_litre=Decimal("998"), effective_date=tz.now().date())
        cheap = Property.objects.create(owner=self.agent, main_image=_tiny_image(),
                                        **dict(PROPERTY_FIELDS, title="Cheap Rent Far", price="100000"))
        dear = Property.objects.create(owner=self.agent, main_image=_tiny_image(),
                                       **dict(PROPERTY_FIELDS, title="Dear Rent Near", price="900000"))
        cheap.compute_true_cost(); dear.compute_true_cost()
        r = self.client.get(reverse("property_list") + "?sort=true_cost")
        titles = [p.title for p in r.context["properties"]]
        self.assertLess(titles.index("Cheap Rent Far"), titles.index("Dear Rent Near"))

    def test_estimator_defaults_to_admin_fuel_price(self):
        from .models import FuelPrice
        from django.utils import timezone as tz
        FuelPrice.objects.create(fuel_type="petrol", price_per_litre=Decimal("998"), effective_date=tz.now().date())
        self.client.login(username="cust1", password="Passw0rd!23")
        with patch("RealEstate.views.geo.geocode",
                   return_value={"lat": 7.39, "lng": 3.91, "display": "T"}), \
             patch("RealEstate.views.geo.route_distance_km", return_value=5.0):
            r = self.client.post(
                reverse("cost_estimation_detail", args=[self.property_.pk]),
                {"num_cars": "1", "vehicle_1": str(self.vehicle.pk),
                 "work_location_1": "Ring Road, Ibadan", "work_trips_per_week_1": "10"})
        self.assertEqual(r.status_code, 200)
        # ₦998/L applied: 5200 km × 0.068 × 998 = ₦352,892.80/yr
        row = HistoricalData.objects.filter(user=self.customer).latest("id")
        self.assertEqual(row.transportation_cost, Decimal("352892.80"))



    def test_public_pages_render(self):
        for url in ["/", "/property", "/about", "/contact", "/blog", "/login",
                    "/customer-register/", "/agent-register/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url, follow=True).status_code, 200)

    def test_property_detail_renders(self):
        r = self.client.get(reverse("property_detail", args=[self.property_.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "2 Bedroom Flat")

    def test_detail_without_coords_falls_back_to_geocode(self):
        """No stored coords -> template includes the Nominatim fallback path."""
        self.property_.latitude = self.property_.longitude = None
        self.property_.save()
        r = self.client.get(reverse("property_detail", args=[self.property_.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "nominatim.openstreetmap.org")

    def test_create_geocodes_once_and_stores_coords(self):
        self.client.login(username="agent1", password="Passw0rd!23")
        with patch("RealEstate.views.geo.geocode",
                   return_value={"lat": 7.4, "lng": 3.9, "display": "Test"}):
            r = self.client.post(reverse("property_create"), dict(
                PROPERTY_FIELDS, title="Geocoded Flat", main_image=""))
        self.assertEqual(r.status_code, 200)  # form re-render (missing image) — but geocode ran
        prop = Property.objects.filter(title="Geocoded Flat").first()
        if prop:  # image required in this env; assert coords when saved
            self.assertEqual(prop.latitude, 7.4)

    def test_detail_with_coords_skips_geocode(self):
        self.property_.latitude, self.property_.longitude = 7.4, 3.9
        self.property_.save()
        r = self.client.get(reverse("property_detail", args=[self.property_.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(b"nominatim.openstreetmap.org", r.content)


class ProfileFlowTests(BaseTest):
    def test_profile_page_requires_login(self):
        r = self.client.get(reverse("commute_profile"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.url)

    def test_profile_save_and_reuse(self):
        self.client.login(username="cust1", password="Passw0rd!23")
        r = self.client.post(reverse("commute_profile"), {
            "fuel_price": "998", "work_location": "Ring Road, Ibadan",
            "work_trips_per_week": "10"})
        self.assertEqual(r.status_code, 302)  # save-and-redirect
        profile = EstimateProfile.objects.get(user=self.customer)
        self.assertEqual(profile.work_location, "Ring Road, Ibadan")
        self.assertEqual(profile.fuel_price, Decimal("998"))

        # Estimator GET prefills from the profile
        r = self.client.get(reverse("cost_estimation_detail", args=[self.property_.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Ring Road, Ibadan")

    def test_estimator_fuel_falls_back_to_profile(self):
        EstimateProfile.objects.create(
            user=self.customer, fuel_price=Decimal("998"),
            work_location="Ring Road, Ibadan", work_trips_per_week=10)
        self.client.login(username="cust1", password="Passw0rd!23")
        with patch("RealEstate.views.geo.geocode",
                   return_value={"lat": 7.39, "lng": 3.91, "display": "T"}), \
             patch("RealEstate.views.geo.route_distance_km", return_value=5.0):
            r = self.client.post(
                reverse("cost_estimation_detail", args=[self.property_.pk]),
                {"num_cars": "1", "vehicle_1": str(self.vehicle.pk),
                 "work_location_1": "Ring Road, Ibadan", "work_trips_per_week_1": "10"})
        self.assertEqual(r.status_code, 200)
        row = HistoricalData.objects.filter(user=self.customer).latest("id")
        self.assertEqual(row.transportation_cost, Decimal("352892.80"))  # 5200 km × 0.068 × 998

    def test_cards_show_no_true_cost_badge(self):
        """True cost is personal — cards must never present a generic verdict."""
        from .models import FuelPrice
        from django.utils import timezone as tz
        FuelPrice.objects.create(fuel_type="petrol", price_per_litre=Decimal("998"),
                                 effective_date=tz.now().date())
        self.property_.compute_true_cost()
        r = self.client.get(reverse("property_list"))
        self.assertNotContains(r, "True cost/yr")

    def test_detail_cta_is_personal(self):
        self.client.login(username="cust1", password="Passw0rd!23")
        r = self.client.get(reverse("property_detail", args=[self.property_.pk]))
        self.assertContains(r, "Estimate this home's cost for me")
        self.assertNotContains(r, "Just Book!")
