from pathlib import Path


def test_backend_env_example_has_required_keys():
    env_path = Path(__file__).resolve().parents[2] / "backend" / ".env.example"
    text = env_path.read_text()
    required_keys = [
        "APP_ENV",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "JWT_SECRET",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
        "UBER_CLIENT_ID",
        "UBER_CLIENT_SECRET",
    ]
    for key in required_keys:
        assert f"{key}=" in text


def test_frontend_env_example_exists():
    env_path = Path(__file__).resolve().parents[2] / "frontend" / ".env.example"
    assert env_path.exists()
    text = env_path.read_text()
    assert "VITE_API_BASE_URL=" in text

