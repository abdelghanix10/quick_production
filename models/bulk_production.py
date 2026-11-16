from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class QuickProductionList(models.TransientModel):
    _name = 'quick.production.list'
    _description = 'Quick Bulk Production List'

    mo_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(related='mo_id.product_id', string='Product', readonly=True)
    uom_id = fields.Many2one(related='mo_id.product_uom_id', string='UoM', readonly=True)
    date_start = fields.Datetime(related='mo_id.date_start', string='Scheduled Date', readonly=True)
    qty_producing = fields.Float(string='Quantity to Produce', default=0.0)
    state = fields.Selection(related='mo_id.state', string='State', readonly=True)

    qty_total = fields.Float(related='mo_id.product_qty', string='Planned Qty', readonly=True)
    qty_total_str = fields.Char(string='Total Label', compute='_compute_qty_total_str')

    @api.depends('qty_total', 'uom_id')
    def _compute_qty_total_str(self):
        for record in self:
            uom_name = record.uom_id.name or ''
            record.qty_total_str = f"/ {record.qty_total:.2f} {uom_name}".strip()

    @api.constrains('qty_producing', 'qty_total')
    def _check_qty_producing_limit(self):
        for record in self:
            if record.qty_producing < 0:
                raise ValidationError(_("Quantity to produce cannot be negative."))
            if record.qty_producing > record.qty_total:
                raise ValidationError(
                    _("Quantity to produce (%(prod).2f) cannot exceed planned quantity (%(plan).2f). Use 'Edit' to increase planned quantity.",
                      prod=record.qty_producing, plan=record.qty_total)
                )

    def action_fill_planned_qty(self):
        """Sets qty_producing = qty_total on all selected lines."""
        for record in self:
            record.qty_producing = record.qty_total
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_edit_qty(self):
        self.ensure_one()
        return {
            'name': _('Edit Planned Quantity'),
            'type': 'ir.actions.act_window',
            'res_model': 'quick.production.edit.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mo_id': self.mo_id.id,
                'default_new_qty': self.qty_total,
                'default_quick_list_id': self.id,
            },
        }

    def action_cancel(self):
        """Cancels the Manufacturing Order."""
        self.ensure_one()
        self.mo_id.action_cancel()
        self.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_produce_line(self):
        """Produces a single line."""
        self.ensure_one()
        if self.qty_producing <= 0:
            raise UserError(_("Quantity must be strictly positive."))
        if self.qty_producing > self.qty_total:
            raise UserError(
                _("Quantity to produce (%(prod).2f) cannot exceed planned quantity (%(plan).2f).",
                  prod=self.qty_producing, plan=self.qty_total)
            )
        self._complete_mo(self.mo_id, self.qty_producing)
        return self.env.ref('quick_production.action_open_bulk_production')._run_action_code_multi()

    def action_produce_selected(self):
        """Produces all selected lines with positive quantity."""
        produced_count = 0
        for record in self:
            if record.qty_producing > 0:
                if record.qty_producing > record.qty_total:
                    raise UserError(
                        _("Quantity to produce (%(prod).2f) cannot exceed planned quantity (%(plan).2f) for %(product)s.",
                          prod=record.qty_producing, plan=record.qty_total, product=record.product_id.display_name)
                    )
                record._complete_mo(record.mo_id, record.qty_producing)
                produced_count += 1

        if produced_count == 0:
            raise UserError(_("Please enter a positive quantity on at least one selected order."))

        return self.env.ref('quick_production.action_open_bulk_production')._run_action_code_multi()

    @api.model
    def _complete_mo(self, mo, qty):
        """Completes the MO cleanly, handling partial backorders and consumption warnings."""
        if mo.state == 'draft':
            mo.action_confirm()

        mo.qty_producing = qty

        for move in mo.move_raw_ids:
            if move.state not in ('done', 'cancel'):
                if mo.product_qty > 0:
                    factor = qty / mo.product_qty
                    move.quantity = move.product_uom_qty * factor
                    move.picked = True

        res = mo.with_context(skip_Expired=True).button_mark_done()

        # Handle wizards returned by button_mark_done (Backorder, Immediate, Consumption Warning)
        while isinstance(res, dict) and res.get('res_model'):
            res_model = res['res_model']
            ctx = res.get('context', {})
            if res_model == 'mrp.production.backorder':
                wiz = self.env[res_model].with_context(ctx).create({})
                res = wiz.action_backorder()
            elif res_model == 'mrp.immediate.production':
                wiz = self.env[res_model].with_context(ctx).create({})
                res = wiz.process()
            elif res_model == 'mrp.consumption.warning':
                wiz = self.env[res_model].with_context(ctx).create({})
                res = wiz.action_confirm()
            else:
                break

        if mo.state == 'to_close':
            mo.button_mark_done()