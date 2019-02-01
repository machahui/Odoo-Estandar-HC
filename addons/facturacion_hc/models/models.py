
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
import decimal

class FactElecSerie(models.Model):
    _name = 'factelec.serie'

    name = fields.Char(string='Serie de Facturacion', size=4)
    type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento', required=True)
    sequence_id = fields.Many2one('ir.sequence', string='Secuencia', required=True)
    sequence_number_next = fields.Integer(string='Siguiente numero', compute='_compute_seq_number_next', inverse='_inverse_seq_number_next')
    description = fields.Char(string='Descripcion')
    is_factelec = fields.Boolean(string='¿Es electronica?', default=False)

    @api.multi
    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        if self.sequence_id:
            sequence = self.sequence_id._get_current_sequence()
            self.sequence_number_next = sequence.number_next_actual
        else:
            self.sequence_number_next = 1

    @api.multi
    def _inverse_seq_number_next(self):
        if self.sequence_id and self.sequence_number_next:
            sequence = self.sequence_id._get_current_sequence()
            sequence.sudo().number_next = self.sequence_number_next
    
    @api.onchange('is_factelec')
    def _onchange_is_factelec(self):
        if self.is_factelec:
            if self.type_document_id.id == 2:
                self.name="F"+self.name
            elif self.type_document_id.id == 4:
                self.name="B"+self.name
        else:
            if self.type_document_id.id in [2, 4]:
                self.name=self.name[1:]


class account_tax(models.Model):
        _inherit = 'account.tax'
        ebill_tax_type = fields.Selection([('1', 'Gravado - Operación Onerosa'),
                                        ('2', 'Gravado – Retiro por premio'),
                                        ('3', 'Gravado – Retiro por donación'),
                                        ('4', 'Gravado – Retiro'),
                                        ('5', 'Gravado – Retiro por publicidad'),
                                        ('6', 'Gravado – Bonificaciones'),
                                        ('7', 'Gravado – Retiro por entrega a trabajadores'),
                                        ('8', 'Exonerado - Operación Onerosa'),
                                        ('9', 'Inafecto - Operación Onerosa'),
                                        ('10', 'Inafecto – Retiro por Bonificación'),
                                        ('11', 'Inafecto – Retiro'),
                                        ('12', 'Inafecto – Retiro por Muestras Médicas'),
                                        ('13', 'Inafecto - Retiro por Convenio Colectivo'),
                                        ('14', 'Inafecto – Retiro por premio'),
                                        ('15', 'Inafecto - Retiro por publicidad'),
                                        ('16', 'Exportación'),], 'F.E. Tipo de Impuesto')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento', domain=[('is_active', 'in', (True))])
    serie_id = fields.Many2one('factelec.serie', 'Serie')
    numero = fields.Char(string='Número')

    @api.onchange('type_document_id')
    def onchange_type_document_id(self):
        if self.type_document_id:
            result = {'domain' :{'serie_id' : [('type_document_id','=',self.type_document_id.id)]}}
            self.serie_id=""
            return result

    #F:factura B:boleta / si es contingencia debe empezar con 0
    @api.one
    def generate_numero_document(self):
        if self.serie_id:
            seq = self.env['ir.sequence'].search([('name', '=', self.serie_id.sequence_id.name)])
            next_number = seq.number_next_actual
            padding = self.serie_id.sequence_id.padding
            self.numero = "0" * (padding - len(str(next_number))) + str(next_number)
        else:
            self.numero = ""
    
    @api.multi
    def create_name(self):
        self.number = self.type_document_id.code + '/' + self.serie_id.name + '-' + self.numero

    def change_type_document_id(self):
        if self.type == 'out_refund':
            result = {'default' :{'type_document_id' : 8}}
            self.serie_id=""
            return result

    @api.multi
    def action_invoice_open(self):
        self.generate_numero_document()
        t = super(AccountInvoice, self).action_invoice_open()
        self.create_name()
        return t

    @api.model
    def create(self, vals):
        onchanges = {
            '_onchange_partner_id': ['account_id', 'payment_term_id', 'fiscal_position_id', 'partner_bank_id'],
            '_onchange_journal_id': ['currency_id'],
        }
        for onchange_method, changed_fields in onchanges.items():
            if any(f not in vals for f in changed_fields):
                invoice = self.new(vals)
                getattr(invoice, onchange_method)()
                for field in changed_fields:
                    if field not in vals and invoice[field]:
                        vals[field] = invoice._fields[field].convert_to_write(invoice[field], invoice)
        if not vals.get('account_id',False):
            raise UserError(_('Configuration error!\nCould not find any account to create the invoice, are you sure you have a chart of account installed?'))

        #Si se trata de una rectificacion
        if vals.get('type') == 'out_refund' or vals.get('type') == 'in_refund':
            vals.update({
                'type_document_id': 8
            })
        
        invoice = super(AccountInvoice, self.with_context(mail_create_nolog=True)).create(vals)
        if any(line.invoice_line_tax_ids for line in invoice.invoice_line_ids) and not invoice.tax_line_ids:
            invoice.compute_taxes()
        
        return invoice