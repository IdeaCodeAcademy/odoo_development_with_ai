from . import models


def post_init_hook(env):
    precision = env['decimal.precision'].search([('name', '=', 'Product Unit')])
    if precision.digits < 3:
        precision.write({'digits': 3})
