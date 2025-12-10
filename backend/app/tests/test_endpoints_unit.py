from datetime import date, datetime

from app.api.endpoints import fleet_orgs, fleet_drivers, fleet_vehicles, fleet_metrics, fleet_payments
from app.schemas.org import Org
from app.schemas.driver import Driver
from app.schemas.vehicle import Vehicle
from app.schemas.metrics import DriverMetrics
from app.schemas.payments import DriverPayment


class FakeQuery:
    def __init__(self, data):
        self.data = data
        self._filters = []

    def all(self):
        return self.data

    def offset(self, _):
        return self

    def limit(self, _):
        return self

    def filter(self, *_):
        return self

    def order_by(self, *_):
        return self

    def first(self):
        return self.data[0] if self.data else None


class FakeDB:
    def __init__(self, payload):
        self.payload = payload

    def query(self, _model):
        return FakeQuery(self.payload)

    def get(self, _model, key):
        for item in self.payload:
            if getattr(item, "uuid", None) == key or getattr(item, "id", None) == key:
                return item
        return None


def test_list_orgs_returns_data():
    db = FakeDB([Org(id="1", org_id="orgA", name="Org1")])
    result = fleet_orgs.list_orgs(current_user={"org_id": "orgA"}, db=db)  # type: ignore
    assert len(result) == 1
    assert result[0].id == "1"


def test_list_drivers_returns_data():
    db = FakeDB([Driver(uuid="d1", org_id="orgA", name="John", email=None)])
    res = fleet_drivers.list_drivers(current_user={"org_id": "orgA"}, db=db)  # type: ignore
    assert res[0].uuid == "d1"


def test_get_driver_returns_one():
    driver = Driver(uuid="d2", org_id="orgA", name="Jane", email=None)
    db = FakeDB([driver])
    res = fleet_drivers.get_driver("d2", current_user={"org_id": "orgA"}, db=db)  # type: ignore
    assert res.uuid == "d2"


def test_list_vehicles_returns_data():
    vehicle = Vehicle(uuid="v1", org_id="orgA", plate="AA-123-BB", model="Toyota")
    db = FakeDB([vehicle])
    res = fleet_vehicles.list_vehicles(current_user={"org_id": "orgA"}, db=db)  # type: ignore
    assert res[0].plate == "AA-123-BB"


def test_get_vehicle_returns_one():
    vehicle = Vehicle(uuid="v2", org_id="orgA", plate="AA-999-ZZ", model="Tesla")
    db = FakeDB([vehicle])
    res = fleet_vehicles.get_vehicle("v2", current_user={"org_id": "orgA"}, db=db)  # type: ignore
    assert res.uuid == "v2"


def test_driver_metrics_filters_range():
    metric = DriverMetrics(org_id="orgA", driver_uuid="d3", day=date(2024, 1, 1), trips=1, online_hours=2, on_trip_hours=1, earnings=10)
    db = FakeDB([metric])
    res = fleet_metrics.driver_metrics("d3", current_user={"org_id": "orgA"}, db=db, start=date(2023, 12, 31), end=date(2024, 1, 2))  # type: ignore
    assert res[0].driver_uuid == "d3"


def test_driver_payments_filters_range():
    payment = DriverPayment(
        id="p1",
        org_id="orgA",
        driver_uuid="d4",
        occurred_at=datetime(2024, 1, 1, 12, 0),
        amount=100,
        currency="EUR",
        description=None,
    )
    db = FakeDB([payment])
    res = fleet_payments.driver_payments("d4", current_user={"org_id": "orgA"}, db=db, start=date(2023, 12, 31), end=date(2024, 1, 2))  # type: ignore
    assert res[0].amount == 100

