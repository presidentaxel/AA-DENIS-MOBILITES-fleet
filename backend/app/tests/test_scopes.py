from app.uber_integration.uber_scopes import SUPPLIER_SCOPES


def test_uber_scopes_not_empty_and_unique():
    assert SUPPLIER_SCOPES, "Scopes list should not be empty"
    assert len(SUPPLIER_SCOPES) == len(set(SUPPLIER_SCOPES)), "Scopes should be unique"

