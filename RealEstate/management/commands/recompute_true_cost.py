"""Recompute the true-cost cache for all (or priced-since) properties."""
from django.core.management.base import BaseCommand
from RealEstate.models import Property


class Command(BaseCommand):
    help = "Refresh the true-cost cache on all properties (e.g. after a fuel price change)."

    def handle(self, *args, **options):
        missing_fuel = None
        done = 0
        for p in Property.objects.all():
            result = p.compute_true_cost()
            if result is not None:
                done += 1
            elif missing_fuel is None:
                missing_fuel = True
        self.stdout.write(f"Recomputed true cost for {done} property(ies).")
        if missing_fuel:
            self.stdout.write(self.style.WARNING(
                "Some properties skipped — no fuel price set. Add one in admin (FuelPrice)."))
