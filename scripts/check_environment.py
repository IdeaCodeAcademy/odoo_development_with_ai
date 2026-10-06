"""Smoke check the running development environment with standard Python."""
import subprocess
from urllib.request import urlopen

subprocess.run(["docker", "compose", "config", "--quiet"], check=True)
subprocess.run(
    ["docker", "compose", "exec", "-T", "db", "pg_isready", "-U", "odoo"],
    check=True,
)
with urlopen("http://127.0.0.1:8071/web/database/selector", timeout=15) as response:
    assert response.status == 200, response.status
    assert b"Odoo" in response.read(), "Expected Odoo database page"
print("Environment smoke checks passed")
