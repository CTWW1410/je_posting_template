# -*- coding:utf-8 -*-
from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_template = fields.Many2one('posting.template', 'Template', ondelete='set null', copy=False, domain=[('state', '=', 'confirm')])

    @api.onchange('x_template')
    def onchange_template(self):
        self.line_ids = False
        self.ref = self.x_template.ref
        temp = []
        for line in self.x_template.line_ids:
            temp.append({
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id,
                'name': line.name,
                'debit': line.debit,
                'credit': line.credit,
                'tax_line_id': line.tax_line_id,
                'tax_ids': line.tax_ids
            })
        self.update({
            'line_ids': temp
        })
