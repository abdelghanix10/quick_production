from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QuickProductionWizard(models.TransientModel):
    _name = 'quick.production.wizard'
    _description = 'Quick Production Wizard'

    product_id = fields.Many2one('product.product', string='Product', required=True, readonly=True)
    uom_id = fields.Many2one(related='product_id.uom_id', string='Unit of Measure', readonly=True)
    qty_producing = fields.Float(string='Quantity to Produce', default=1.0, required=True)
    has_bom = fields.Boolean(string='Has BOM', compute='_compute_has_bom')
    has_stock_warning = fields.Boolean(string='Stock Shortage Warning', compute='_compute_stock_warning')
    ingredient_ids = fields.One2many(
        'quick.production.wizard.line',
        'wizard_id',
        string='Ingredients',
        readonly=True,
    )

    def _get_bom(self, product):
        """Finds the active BOM for the product."""
        if not product:
            return False
        return self.env['mrp.bom']._bom_find(product).get(product, False)

    @api.depends('product_id')
    def _compute_has_bom(self):
        for rec in self:
            rec.has_bom = bool(rec._get_bom(rec.product_id))

    @api.depends('ingredient_ids.is_shortage')
    def _compute_stock_warning(self):
        for rec in self:
            rec.has_stock_warning = any(rec.ingredient_ids.mapped('is_shortage'))

    @api.onchange('qty_producing', 'product_id')
    def _onchange_qty_producing(self):
        """Calculates required ingredients based on BOM and checks current stock."""
        if not self.product_id:
            return

        bom = self._get_bom(self.product_id)
        commands = [fields.Command.clear()]

        if bom and bom.product_qty > 0 and self.qty_producing > 0:
            factor = self.qty_producing / bom.product_qty
            _boms, lines_done = bom.explode(self.product_id, factor)

            for bom_line, line_data in lines_done:
                comp = bom_line.product_id
                req_qty = line_data['qty']
                commands.append(fields.Command.create({
                    'product_id': comp.id,
                    'qty': req_qty,
                    'qty_available': comp.qty_available,
                    'uom_id': bom_line.product_uom_id.id,
                }))

        self.ingredient_ids = commands

    # Quick Kiosk Quantity Increment Buttons
    def _reopen_wizard(self):
        self._onchange_qty_producing()
        return {
            'name': _('Register Production: %s', self.product_id.display_name),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_add_1(self):
        self.qty_producing += 1.0
        return self._reopen_wizard()

    def action_add_5(self):
        self.qty_producing += 5.0
        return self._reopen_wizard()

    def action_add_10(self):
        self.qty_producing += 10.0
        return self._reopen_wizard()

    def action_add_50(self):
        self.qty_producing += 50.0
        return self._reopen_wizard()

    def action_reset_qty(self):
        self.qty_producing = 1.0
        return self._reopen_wizard()

    def _create_confirmed_mo(self):
        """Helper to create and confirm the Manufacturing Order."""
        self.ensure_one()
        if self.qty_producing <= 0:
            raise UserError(_("Quantity must be strictly positive."))

        bom = self._get_bom(self.product_id)
        mo_vals = {
            'product_id': self.product_id.id,
            'product_qty': self.qty_producing,
            'product_uom_id': self.product_id.uom_id.id,
            'bom_id': bom.id if bom else False,
            'user_id': self.env.uid,
        }
        mo = self.env['mrp.production'].create(mo_vals)
        mo.action_confirm()
        mo.qty_producing = self.qty_producing
        return mo

    def action_confirm(self):
        """Creates and immediately completes (marks Done) the Manufacturing Order."""
        mo = self._create_confirmed_mo()
        self.env['quick.production.list']._complete_mo(mo, self.qty_producing)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Production Completed'),
                'message': _('%(qty).2f %(uom)s of %(product)s marked as Done (%(mo)s).',
                             qty=self.qty_producing,
                             uom=self.uom_id.name,
                             product=self.product_id.display_name,
                             mo=mo.name),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_to_close(self):
        """Creates and confirms the Manufacturing Order, leaving it in Pending Production."""
        mo = self._create_confirmed_mo()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Production Queued'),
                'message': _('Order %(mo)s queued in Pending Production.', mo=mo.name),
                'type': 'info',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }


class QuickProductionWizardLine(models.TransientModel):
    _name = 'quick.production.wizard.line'
    _description = 'Quick Production Wizard Ingredient'

    wizard_id = fields.Many2one('quick.production.wizard', string='Wizard', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Ingredient')
    qty = fields.Float(string='Required Qty')
    qty_available = fields.Float(string='On-Hand Qty')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    is_shortage = fields.Boolean(string='Shortage', compute='_compute_stock_status')
    stock_status = fields.Selection(
        [('available', 'Available'), ('shortage', 'Shortage')],
        string='Stock Status',
        compute='_compute_stock_status',
    )

    @api.depends('qty', 'qty_available')
    def _compute_stock_status(self):
        for line in self:
            shortage = line.qty_available < line.qty
            line.is_shortage = shortage
            line.stock_status = 'shortage' if shortage else 'available'


class QuickProductionEditWizard(models.TransientModel):
    _name = 'quick.production.edit.wizard'
    _description = 'Edit Production Quantity Wizard'

    mo_id = fields.Many2one('mrp.production', string='Manufacturing Order', required=True, readonly=True)
    product_id = fields.Many2one(related='mo_id.product_id', string='Product', readonly=True)
    current_qty = fields.Float(string='Planned Quantity', related='mo_id.product_qty', readonly=True)
    new_qty = fields.Float(string='New Quantity', required=True)
    line_ids = fields.One2many('quick.production.edit.wizard.line', 'wizard_id', string='Ingredients')
    quick_list_id = fields.Many2one('quick.production.list', string='Quick List Item')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_mo_id'):
            mo = self.env['mrp.production'].browse(self.env.context['default_mo_id'])
            lines = []
            for move in mo.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                qty_per_unit = move.product_uom_qty / mo.product_qty if mo.product_qty else 0.0
                lines.append(fields.Command.create({
                    'product_id': move.product_id.id,
                    'qty_per_unit': qty_per_unit,
                    'qty': move.product_uom_qty,
                    'uom_id': move.product_uom.id,
                    'move_id': move.id,
                }))
            res['line_ids'] = lines
        return res

    @api.onchange('new_qty')
    def _onchange_new_qty(self):
        for line in self.line_ids:
            line.qty = line.qty_per_unit * self.new_qty

    def action_save(self):
        self.ensure_one()
        if self.new_qty <= 0:
            raise UserError(_("Quantity must be strictly positive."))

        self.mo_id.write({
            'product_qty': self.new_qty,
            'qty_producing': self.new_qty,
        })

        for line in self.line_ids:
            if line.move_id:
                line.move_id.write({
                    'product_uom_qty': line.qty,
                    'quantity': line.qty,
                    'picked': True,
                })

        if self.quick_list_id:
            self.quick_list_id.write({'qty_producing': self.new_qty})

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class QuickProductionEditWizardLine(models.TransientModel):
    _name = 'quick.production.edit.wizard.line'
    _description = 'Quick Production Edit Wizard Ingredient'

    wizard_id = fields.Many2one('quick.production.edit.wizard', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Ingredient', readonly=True)
    qty_per_unit = fields.Float(string='Qty per Unit')
    qty = fields.Float(string='New Required Qty')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    move_id = fields.Many2one('stock.move', string='Stock Move')