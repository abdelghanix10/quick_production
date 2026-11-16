from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    production_category_id = fields.Many2one(
        'product.category',
        string='Primary Production Category',
        store=True,
    )
    production_category_ids = fields.Many2many(
        'product.category',
        'res_users_quick_prod_categ_rel',
        'user_id',
        'categ_id',
        string='Additional Production Categories',
    )

    def _get_allowed_production_category_ids(self):
        """Return all allowed category IDs (primary + additional) for the current user."""
        self.ensure_one()
        categs = self.production_category_id | self.production_category_ids
        return categs.ids