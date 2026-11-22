"""
Seed demo data for ComfyHome.

Usage: python manage.py seed_demo [--force]

Idempotent by default: skips if the demo agent already has listings.
No network required: coordinates are precomputed and images are generated
locally with Pillow (zero cost, reproducible).
"""
import random

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction

from RealEstate.models import Property, PropertyImage, User, Vehicle, HistoricalData
from decimal import Decimal

# (Ibadan & Lagos) area name -> approximate (lat, lng)
LOCATIONS = {
    "Bodija":      (7.4173, 3.9021),
    "Akobo":       (7.4097, 3.9287),
    "Agbowo (UI)": (7.4466, 3.9005),
    "Ring Road":   (7.3650, 3.8627),
    "Moniya":      (7.5075, 3.8948),
    "Odo Ona":     (7.3400, 3.8850),
    "Challenge":   (7.3393, 3.8786),
    "Dugbe":       (7.3770, 3.8790),
    "Jericho":     (7.4020, 3.8820),
    "Basorun":     (7.4280, 3.9130),
    "Yaba":        (6.5158, 3.3898),
    "Surulere":    (6.4930, 3.3560),
    "Ikeja":       (6.6018, 3.3515),
    "Lekki Ph 1":  (6.4433, 3.4738),
    "Ajah":        (6.4667, 3.5670),
}

DEMO_USERS = {
    "demoagent": {"is_agent": True, "first_name": "Adebola", "last_name": "Properties"},
    "democust":  {"is_agent": False, "is_customer": True, "first_name": "Kabir", "last_name": "O."},
}
DEMO_PASSWORD = "ComfyDemo2026!"

# title, area, type(Apartment/House/Condo), beds, baths, sqft, price(₦/yr), description
PROPERTIES = [
    ("2 Bedroom Flat", "Akobo", "Apartment", 2, 2, 300, 900_000,
     "Spacious 2-bedroom flat in a gated estate off Akobo Road. Prepaid meter, borehole, secure parking. Landlord accepts 60/40 instalments."),
    ("Self Contain", "Agbowo (UI)", "Apartment", 1, 1, 240, 700_000,
     "Self contain apartment walking distance to UI main gate. All needed infrastructures confirmed available and working."),
    ("3 Bedroom Duplex", "Bodija", "House", 3, 4, 180, 1_800_000,
     "Well-finished 3-bedroom duplex in Old Bodija. Compound parking, water treatment, quiet neighbourhood."),
    ("Mini Flat", "Moniya", "Apartment", 1, 1, 450, 450_000,
     "Brand new mini flat in a quiet Moniya estate. Borehole water and security. Long commute to city centre — check the true-cost estimate!"),
    ("1 Bedroom Flat", "Ring Road", "Apartment", 1, 1, 280, 850_000,
     "Neat 1-bedroom flat along Ring Road commercial hub. Generator backup, prepaid meter."),
    ("2 Bedroom Flat", "Odo Ona", "Apartment", 2, 2, 310, 600_000,
     "2 bedroom flat with 10-feet fence and golden gate at Odo Ona. Family-friendly street, close to schools."),
    ("Studio Apartment", "Dugbe", "Apartment", 1, 1, 220, 950_000,
     "Compact studio in the heart of Dugbe business district. Ideal for young professionals — walk to work."),
    ("4 Bedroom House", "Jericho", "House", 4, 5, 260, 2_400_000,
     "Executive 4-bedroom house in Jericho GRA. Borehole, inverter system, ample parking."),
    ("2 Bedroom Flat", "Basorun", "Apartment", 2, 2, 290, 550_000,
     "Affordable 2-bedroom in Basorun. Tiled floors, POP ceiling, secure estate."),
    ("3 Bedroom Flat", "Challenge", "Apartment", 3, 3, 320, 1_100_000,
     "3-bedroom flat near Challenge roundabout. Shoprite, markets and transport hubs nearby."),
    ("2 Bedroom Flat", "Yaba", "Apartment", 2, 2, 300, 1_400_000,
     "Renovated 2-bedroom flat in Yaba tech district. Close to Neville Hall and CSS bookshops."),
    ("Mini Flat", "Surulere", "Apartment", 1, 1, 260, 650_000,
     "Mini flat in a calm Surulere street. 15 minutes to the Island in light traffic."),
    ("3 Bedroom Flat", "Ikeja", "Apartment", 3, 3, 340, 1_600_000,
     "Serviced 3-bedroom flat in Ikeja GRA. Estate security and water treatment."),
    ("2 Bedroom Apartment", "Lekki Ph 1", "Condo", 2, 3, 310, 2_200_000,
     "Modern 2-bedroom condo in Lekki Phase 1. Gym and swimming pool in the compound."),
    ("Mini Flat", "Ajah", "Apartment", 1, 1, 240, 500_000,
     "Newly built mini flat in Ajah. Affordable but far from the Island — compare true cost first!"),
]

# image tile label, background colour band
IMAGE_STYLES = [
    ("EXTERIOR", (30, 58, 70), (12, 42, 56)),
    ("LIVING ROOM", (44, 84, 104), (24, 60, 84)),
    ("BEDROOM", (72, 62, 92), (48, 44, 72)),
    ("KITCHEN", (58, 92, 78), (34, 66, 58)),
]


def _generate_image(label, style, beds_text, price_text):
    """Draw a branded placeholder tile (no downloads, no external assets)."""
    from PIL import Image, ImageDraw, ImageFont
    w, h = 800, 500
    base, band = style
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    # diagonal band accent
    d.polygon([(0, h), (0, h - 90), (w, h - 260), (w, h)], fill=band)
    # top-left brand strip
    d.rectangle([0, 0, 220, 44], fill=(255, 90, 61))
    try:
        f_brand = ImageFont.load_default(size=22)
        f_head = ImageFont.load_default(size=44)
        f_sub = ImageFont.load_default(size=24)
    except TypeError:  # Pillow < 10.1
        f_brand = f_head = f_sub = ImageFont.load_default()
    d.text((16, 10), "COMFYHOME", font=f_brand, fill="white")
    d.text((40, 150), label, font=f_head, fill="white")
    d.text((40, 220), beds_text, font=f_sub, fill=(210, 225, 232))
    d.text((40, 260), price_text, font=f_sub, fill=(210, 225, 232))
    d.text((40, h - 60), "Demo placeholder image", font=f_brand, fill=(150, 170, 180))
    buf = ContentFile(b"")
    img.save(buf, format="JPEG", quality=82)
    buf.seek(0)
    return buf


class Command(BaseCommand):
    help = "Seed demo users, vehicles, properties (with generated images) and sample estimates."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Seed even if demo data already exists")

    @transaction.atomic
    def handle(self, *args, **options):
        # Admin-managed fuel prices come first — the true-cost cache below
        # needs them even when property seeding is skipped.
        from RealEstate.models import FuelPrice
        if not FuelPrice.objects.exists():
            from django.utils import timezone as tz
            FuelPrice.objects.create(fuel_type="petrol", price_per_litre=Decimal("998.00"),
                                     effective_date=tz.now().date())
            FuelPrice.objects.create(fuel_type="diesel", price_per_litre=Decimal("1150.00"),
                                     effective_date=tz.now().date())

        demo_agent = User.objects.filter(username="demoagent").first()
        if demo_agent and Property.objects.filter(owner=demo_agent).exists() and not options["force"]:
            # Properties already seeded — still refresh the true-cost cache,
            # then skip the rest.
            recomputed = sum(1 for p in Property.objects.all() if p.compute_true_cost() is not None)
            self.stdout.write(f"Demo data already present — refreshed true-cost cache for "
                              f"{recomputed} property(ies) (use --force to re-seed everything).")
            return

        self.stdout.write("Seeding demo data...")

        users = {}
        for username, extra in DEMO_USERS.items():
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
            for field, value in extra.items():
                setattr(user, field, value)
            user.save()
            users[username] = user
        agent, customer = users["demoagent"], users["democust"]

        vehicles = {}
        for name, rate in [("Honda Civic", 0.068), ("Kia Rio", 0.071),
                           ("Toyota Corolla", 0.065), ("Suzuki Danfo-bus", 0.130)]:
            v, _ = Vehicle.objects.get_or_create(
                user=customer, name=name, defaults={"fuel_consumption_rate": rate})
            vehicles[name] = v

        rng = random.Random(42)
        count = 0
        for title, area, ptype, beds, baths, sqft, price, desc in PROPERTIES:
            lat, lng = LOCATIONS[area]
            zip_code = "101233" if area in ("Yaba", "Surulere", "Ikeja", "Lekki Ph 1", "Ajah") else "200261"
            prop, _ = Property.objects.get_or_create(
                title=f"{title}, {area}",
                owner=agent,
                defaults={
                    "description": desc,
                    "address": f"{title.split()[0]} Road, {area}",
                    "city": "Lagos" if zip_code == "101233" else "Ibadan",
                    "state": "Lagos" if zip_code == "101233" else "Oyo",
                    "zip_code": zip_code,
                    "sale_or_rent": "rent",
                    "price": Decimal(price),
                    "property_type": ptype,
                    "bedrooms": beds,
                    "bathrooms": baths,
                    "square_feet": sqft,
                    "latitude": lat,
                    "longitude": lng,
                },
            )
            if prop.main_image:  # already seeded fully
                continue
            for idx, (label, c1, c2) in enumerate(IMAGE_STYLES):
                img = _generate_image(
                    title if idx == 0 else label, (c1, c2),
                    f"{beds} BED  ·  {baths} BATH  ·  {sqft} SQ FT" if idx == 0 else f"{beds} BED  ·  {baths} BATH",
                    f"NGN {price:,} / YEAR  ·  {area.upper()}, "
                    f"{'LAGOS' if zip_code == '101233' else 'IBADAN'}",
                )
                if idx == 0:
                    prop.main_image.save(f"seed_{count}_main.jpg", img, save=True)
                else:
                    extra = PropertyImage(property=prop)
                    extra.image.save(f"seed_{count}_{idx}.jpg", img, save=True)
            count += 1

        # Admin-managed national fuel prices (estimator + true-cost cache)
        # -> moved to the top of handle() so the skip path still refreshes them

        # Sample saved estimates for the demo customer (numbers are plausible
        # pre-computed values — no network calls at seed time)
        if not HistoricalData.objects.filter(user=customer).exists():
            samples = [
                ("Akobo", "Ring Road, Ibadan", 10, Decimal("5200.00"), Decimal("352892.80")),
                ("Agbowo (UI)", "University of Ibadan", 4, Decimal("1560.00"), Decimal("105727.84")),
            ]
            for area, work, trips, dist, transport in samples:
                prop = Property.objects.filter(title__contains=area).first()
                if prop:
                    HistoricalData.objects.create(
                        user=customer, property=prop,
                        vehicle_name="Honda Civic", work_location=work,
                        work_trips_per_week=trips, other_locations="{}",
                        total_distance=dist, transportation_cost=transport,
                        total_effective_cost=prop.price + transport,
                    )

        # Demo admin so you can inspect the admin panel (change this password!)
        if not User.objects.filter(username="demoadmin").exists():
            User.objects.create_superuser("demoadmin", "demoadmin@example.com", DEMO_PASSWORD)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {count} properties, demo agent (demoagent/{DEMO_PASSWORD}), "
            f"demo customer (democust/{DEMO_PASSWORD}), admin (demoadmin/{DEMO_PASSWORD})."))

        # True-cost cache for every property (uses the fuel price above)
        recomputed = sum(1 for p in Property.objects.all() if p.compute_true_cost() is not None)
        self.stdout.write(f"True-cost cache refreshed for {recomputed} property(ies).")
