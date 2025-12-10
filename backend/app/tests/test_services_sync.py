from datetime import date, datetime

from app.uber_integration import services_orgs, services_drivers, services_vehicles, services_metrics, services_payments
from app.models.org import UberOrganization
from app.models.driver import UberDriver
from app.models.vehicle import UberVehicle
from app.models.driver_metrics import DriverDailyMetrics
from app.models.driver_payments import DriverPayment


class FakeDB:
    def __init__(self):
        self.seen = []

    def merge(self, obj):
        self.seen.append(obj)

    def commit(self):
        return None


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def get(self, *_args, **_kwargs):
        return {"data": self.payload}


def test_sync_orgs_merges_rows():
    db = FakeDB()
    client = FakeClient([{"id": "1", "name": "Org"}])
    services_orgs.sync_organizations(db, client)
    assert any(isinstance(obj, UberOrganization) for obj in db.seen)


def test_sync_drivers_merges_rows():
    db = FakeDB()
    client = FakeClient([{"uuid": "d1", "name": "John"}])
    services_drivers.sync_drivers(db, client)
    assert any(isinstance(obj, UberDriver) for obj in db.seen)


def test_sync_vehicles_merges_rows():
    db = FakeDB()
    client = FakeClient([{"uuid": "v1", "license_plate": "AA-123-BB", "model": "Toyota"}])
    services_vehicles.sync_vehicles(db, client)
    assert any(isinstance(obj, UberVehicle) for obj in db.seen)


def test_sync_metrics_merges_rows():
    db = FakeDB()
    client = FakeClient(
        [
            {
                "id": "m1",
                "driver_uuid": "d1",
                "day": "2024-01-01",
                "trips": 2,
                "online_hours": 3,
                "on_trip_hours": 1,
                "earnings": 42.5,
            }
        ]
    )
    services_metrics.sync_metrics(db, client, date(2024, 1, 1), date(2024, 1, 2))
    assert any(isinstance(obj, DriverDailyMetrics) for obj in db.seen)


def test_sync_payments_merges_rows():
    db = FakeDB()
    client = FakeClient(
        [
            {
                "id": "p1",
                "driver_uuid": "d1",
                "occurred_at": datetime(2024, 1, 1, 12, 0).isoformat(),
                "amount": 10.5,
                "currency": "EUR",
            }
        ]
    )
    services_payments.sync_payments(db, client, datetime.utcnow())
    assert any(isinstance(obj, DriverPayment) for obj in db.seen)

