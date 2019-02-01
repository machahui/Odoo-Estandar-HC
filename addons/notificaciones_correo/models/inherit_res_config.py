# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime, timedelta

class Company(models.Model):
    _inherit = 'res.company'
    nopaid_user_id = fields.Many2one('res.users',string = 'Usuario facturacion')
    nogiveback_user_id = fields.Many2one('res.users',string = 'Usuario inventario')
    days_nopaid = fields.Integer(string='Dias de anticipacion')
    days_nogiveback = fields.Integer(string='Dias de sobrepaso')

class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    email_user = fields.Char(string="Email From",related='company_id.email')
    
    nopaid_user_id = fields.Many2one('res.users',related='company_id.nopaid_user_id',string = 'Usuario inventario')
    nopaid_invoices_ids = fields.One2many('nopaid.invoice.transient','nopaid_id',store=True)
    days_nopaid = fields.Integer(string=u'Dias de anticipacion',related='company_id.days_nopaid')
    
    nogiveback_user_id = fields.Many2one('res.users',related='company_id.nogiveback_user_id',string = 'Usuario facturacion')
    nogiveback_tools_ids = fields.One2many('nogiveback.stock.transient','nogiveback_id',store=True)
    days_nogiveback = fields.Integer(string=u'Dias de sobrepaso',related='company_id.days_nogiveback')
    
    #Facturas por pagar
    def action_list_invoices_(self):
        invoices_list=[]
        res = self.env['res.config.settings'].search([],order="id desc", limit=1)
        if res.id:
            res.nopaid_invoices_ids = None
            invoices = self.env['account.invoice'].search([('state', '=', 'open')])
            final_due = datetime.now() + timedelta(days=res.days_nopaid)
            for invoice in invoices:
                if datetime.strptime(invoice.date_due, '%Y-%m-%d') < final_due:
                    invoices_list.append([0,0,{'partner_name':invoice.partner_id.name,
                                        'fact_number':invoice.number,
                                        'amount_total':invoice.amount_total,
                                        'residual':invoice.residual,
                                        'date_due':invoice.date_due}])
            res.nopaid_invoices_ids = invoices_list
            print(">>res.nopaid_invoices_ids", res.nopaid_invoices_ids)
            return 
        else:
            return
    
    def action_nopaid_invoices_send(self):
        self.action_list_invoices_()
        res = self.env['res.config.settings'].search([],order="id desc", limit=1)
        if res.id:
            if res.nopaid_invoices_ids:
                template_id = self.env.ref('notificaciones_correo.nopaid_invoice_email_template')
                send = template_id.send_mail(res.id, force_send=True)
                return True
        return False
    
    #Herramientas no devueltas SOLO FUNCIONA CON DYSCHEM
    def action_list_tools_(self):
        res = self.env['res.config.settings'].search([],order="id desc", limit=1)
        if res.id:
            tools_list=[]
            res.nogiveback_tools_ids = None
            pickings = self.env['stock.picking'].search([('picking_type_id', '=', 8),('state','=','done')])
            final_due = datetime.now() + timedelta(days=res.days_nogiveback)
            for picking in pickings:
                if self.env['stock.picking'].search([('origin', 'like', 'Retorno de '+picking.name)]) or picking.origin:
                    print("No entra ",picking.name)
                else:
                    if datetime.strptime(picking.date_finish, '%Y-%m-%d %H:%M:%S') < final_due:
                        moves_list=""
                        moves = self.env['stock.move'].search([('picking_id', '=', picking.id)])
                        for move in moves:
                            moves_list += '\n'+move.name+' - '+str(move.product_uom_qty)+' '+str(move.product_uom.name)
                        tools_list.append({'responsable_name':picking.responsable_id.name,
                                        'referencia':picking.name,
                                        'tools':moves_list,
                                        'date_finish':picking.date_finish})
            res.nogiveback_tools_ids = tools_list
            print(">>res.nogiveback_tools_ids", res.nogiveback_tools_ids)
            return
        else:
            return
    
    def action_nogiveback_tools_send(self):
        self.action_list_tools_()
        res = self.env['res.config.settings'].search([],order="id desc", limit=1)
        if res.id:
            if res.nogiveback_tools_ids:
                template_id = self.env.ref('notificaciones_correo.nogiveback_tool_email_template')
                send = template_id.send_mail(res.id, force_send=True)
                return True
        return False