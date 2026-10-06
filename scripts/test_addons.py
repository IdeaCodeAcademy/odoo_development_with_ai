"""Run addon tests in a new, isolated database; retain it for diagnosis."""
from pathlib import Path
import subprocess
import tempfile
import uuid


database = 'hair_test_' + uuid.uuid4().hex[:12]
log_path = Path(tempfile.gettempdir()) / (database + '.log')
command = [
    'docker', 'compose', 'run', '--rm', '--no-deps', 'web', 'odoo',
    '-d', database, '-i', 'hair_base,hair_supplier,ica_web_responsive', '--without-demo=true',
    '--test-enable', '--test-tags=/hair_base,/hair_supplier,/ica_web_responsive',
    '--stop-after-init', '--no-http', '--log-level=test',
]
print(f'Test database: {database}; log: {log_path}', flush=True)
with log_path.open('w') as log_file:
    result = subprocess.run(command, stdout=log_file, stderr=subprocess.STDOUT)
print(f'Exit status: {result.returncode}', flush=True)
output = log_path.read_text()
print(output[-6000:])
if result.returncode == 0 and ('Starting TestHairMasterData.' not in output
                             or 'Starting TestLocationSecurity.' not in output
                             or 'Starting TestHairSellers.' not in output
                             or '0 failed, 0 error(s)' not in output):
    raise SystemExit('Expected custom test suites did not complete successfully')
raise SystemExit(result.returncode)
