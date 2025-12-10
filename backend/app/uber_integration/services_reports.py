from sqlalchemy.orm import Session

from app.uber_integration.uber_client import UberClient


def request_report(db: Session, client: UberClient) -> None:
    # Placeholder: trigger report generation (depends on Uber API capabilities).
    client.post("/v1/reports", payload={})

