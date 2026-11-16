from odoo import models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_open_quick_production_wizard(self):
        """Opens the Quick Production Wizard for this product."""
        self.ensure_one()
        return {
            'name': _('Register Production: %s', self.display_name),
            'type': 'ir.actions.act_window',
            'res_model': 'quick.production.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self.id},
        }