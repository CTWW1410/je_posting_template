# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PostingTemplate(models.Model):
    _name = 'posting.template'
    _description = 'Posting Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    name = fields.Char('Code', copy=False, track_visibility='onchange')
    ref = fields.Char('Template Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')
    ], 'State', default='draft', track_visibility='onchange')
    line_ids = fields.One2many('posting.template.line', 'order_id', 'Lines', copy=True)

    _sql_constraints = [('name_uiq', 'unique (name)', "Name must be unique!")]

    def check_balance(self):
        total_debit = sum(line.debit for line in self.line_ids)
        total_credit = sum(line.credit for line in self.line_ids)
        if total_debit != total_credit:
            raise UserError(_('Total Debit is not equals total Credit!'))

    def button_confirm(self):
        self.check_balance()
        self.line_ids.check_debit_credit()
        if not self.line_ids:
            raise UserError(_('You need at least 2 lines in the journal entry!'))
        self.state = 'confirm'

    def set_to_draft(self):
        self.state = 'draft'

    @api.onchange('line_ids')
    def create_tax_line(self):
        for rec in self:
            tax_lines = []
            if rec.line_ids.filtered(lambda r: r.recompute_tax_line):
                for lo in rec.line_ids.filtered(lambda r: r.tick):
                    rec.line_ids -= lo
                for line in rec.line_ids:
                    cur_round = line.account_id.currency_id.decimal_places if line.account_id.currency_id.decimal_places \
                        else line.account_id.company_id.currency_id.decimal_places
                    line.recompute_tax_line = False
                    for tax in line.tax_ids:
                        tax_lines.append({
                            'order_id': rec.id,
                            'account_id': tax.account_id.id,
                            'partner_id': line.partner_id.id,
                            'name': tax.name,
                            'debit': round(line.debit * tax.amount / 100, cur_round) if line.debit != 0 else 0,
                            'credit': round(line.credit * tax.amount / 100, cur_round) if line.credit != 0 else 0,
                            'tax_line_id': tax.id,
                            'tick': True
                        })
                tax_id_group = {}
                for r in tax_lines:
                    if r.get('debit') and str(r.get('tax_line_id'))+'_debit' in tax_id_group:
                        tax_id_group[str(r.get('tax_line_id'))+'_debit']['debit'] += r.get('debit', 0)
                    elif r.get('credit') and str(r.get('tax_line_id'))+'_credit' in tax_id_group:
                        tax_id_group[str(r.get('tax_line_id'))+'_credit']['credit'] += r.get('credit', 0)
                    elif r.get('debit') and str(r.get('tax_line_id'))+'_debit' not in tax_id_group:
                        tax_id_group[str(r.get('tax_line_id'))+'_debit'] = r
                    elif r.get('credit') and str(r.get('tax_line_id'))+'_credit' not in tax_id_group:
                        tax_id_group[str(r.get('tax_line_id'))+'_credit'] = r

                val_line = []
                for li in tax_id_group:
                    val_line.append((0, 0, tax_id_group[li]))
                rec.update({
                    'line_ids': val_line
                })

    def unlink(self):
        for rec in self:
            if rec.state == 'confirm':
                raise UserError(_('You can only delete draft document!'))
        return super(PostingTemplate, self).unlink()

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.update({
            'name': self.name + ' (copy)',
        })
        return super(PostingTemplate, self).copy(default=default)


class PostingTemplateLine(models.Model):
    _name = 'posting.template.line'

    @api.model
    def _get_currency(self):
        currency = False
        context = self._context or {}
        if context.get('default_journal_id', False):
            currency = self.env['account.journal'].browse(context['default_journal_id']).currency_id
        return currency

    order_id = fields.Many2one('posting.template', 'Header', ondelete='cascade')
    account_id = fields.Many2one('account.account', 'Account', ondelete='restrict')
    partner_id = fields.Many2one('res.partner', 'Partner', ondelete='restrict')
    name = fields.Char('Label')
    debit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    company_id = fields.Many2one('res.company', related='account_id.company_id', string='Company', store=True,
                                 readonly=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True,
                                          help='Utility field to express amount currency', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=_get_currency,
                                  help="The optional other currency if it is a multi-currency entry.")
    tax_ids = fields.Many2many('account.tax', string='Taxes Applied',
                               domain=['|', ('active', '=', False), ('active', '=', True)],
                               help="Taxes that apply on the base amount")
    tax_line_id = fields.Many2one('account.tax', string='Originator tax', ondelete='restrict',
                                  help="Indicates that this journal item is a tax line")
    product_id = fields.Many2one('product.product', 'Product')
    tick = fields.Boolean('Auto Tax')
    recompute_tax_line = fields.Boolean(store=False, default=False)

    @api.onchange('debit', 'credit', 'tax_ids',)
    def onchange_tax_ids_create_aml(self):
        for line in self:
            line.recompute_tax_line = False if line.tick == True else True

    @api.multi
    def check_debit_credit(self):
        for rec in self:
            if rec.debit and rec.credit:
                raise UserError(_('Wrong credit or debit value in accounting entry! Credit or debit should be zero.'))
