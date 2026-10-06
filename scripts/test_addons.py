"""Run addon tests in a new, isolated database; retain it for diagnosis."""
import logging
import subprocess
import tempfile
import uuid
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
_logger = logging.getLogger(__name__)

database = 'hair_test_' + uuid.uuid4().hex[:12]
log_path = Path(tempfile.gettempdir()) / (database + '.log')
command = [
    'docker', 'compose', 'run', '--rm', '--no-deps', 'web', 'odoo',
    '-d', database, '-i', 'hair_base,hair_supplier,hair_purchase,ica_web_responsive', '--without-demo=true',
    '--test-enable', '--test-tags=/hair_base,/hair_supplier,/hair_purchase,/ica_web_responsive',
    '--stop-after-init', '--no-http', '--log-level=test',
]
_logger.info('Test database: %s; log: %s', database, log_path)
with log_path.open('w', encoding='utf-8') as log_file:
    result = subprocess.run(command, stdout=log_file, stderr=subprocess.STDOUT, check=False)
_logger.info('Exit status: %s', result.returncode)
output = log_path.read_text(encoding='utf-8')
_logger.info('%s', output[-6000:])
if result.returncode == 0 and ('Starting TestHairMasterData.' not in output
                             or 'Starting TestLocationSecurity.' not in output
                             or 'Starting TestHairSellers.' not in output
                             or 'Starting TestHairIntake.' not in output
                             or 'Starting TestHairPricing.' not in output
                             or '0 failed, 0 error(s)' not in output):
    message = 'Expected custom test suites did not complete successfully'
    raise SystemExit(message)
raise SystemExit(result.returncode)
