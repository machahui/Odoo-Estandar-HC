# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class nopaid_invoice(models.TransientModel):
    _name='nopaid.invoice.transient'
    
    partner_name=fields.Char(string='Socio')
    fact_number=fields.Char(string='Factura')
    amount_total=fields.Float(string='Cantidad total')
    residual=fields.Float(string='Cantidad a pagar')
    date_due=fields.Date(string='Fecha de vencimiento')
    nopaid_id=fields.Many2one('res.config.settings')

class nogiveback_stock(models.TransientModel):
    _name='nogiveback.stock.transient'
    
    referencia=fields.Char(string='Referencia')
    responsable_name=fields.Char(string='Responsable')
    tools=fields.Char(string='Herramientas')
    date_finish=fields.Date(string='Fecha de entrega')
    nogiveback_id=fields.Many2one('res.config.settings')