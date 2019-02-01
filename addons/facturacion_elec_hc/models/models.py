# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime
import urllib.request
import json
import pytz
import decimal
import pprint
import codecs
import webbrowser
from openerp.osv import osv

class CredentialsNubefact(models.Model):
        _name = 'credentials.nubefact'
        serial_id = fields.Many2one('factelec.serie', 'Serie')
        token_nubefact = fields.Char(u'Token NubeFact')
        url_nubefact = fields.Char(u'URL NubeFact')

class AccountInvoiceInherit(models.Model):
        _inherit = 'account.invoice'
        sunat_transaction_type = fields.Selection([
                ('1',u'VENTA INTERNA'),
                ('2',u'EXPORTACIÓN'),
                ('3',u'NO DOMICILIADO'),
                ('4',u'VENTA INTERNA – ANTICIPOS'),
                ('5',u'VENTA ITINERANTE'),
                ('6',u'FACTURA GUÍA'),
                ('7',u'VENTA ARROZ PILADO'),
                ('8',u'FACTURA - COMPROBANTE DE PERCEPCIÓN'),
                ('10',u'FACTURA - GUÍA REMITENTE'),
                ('11',u'FACTURA - GUÍA TRANSPORTISTA'),
                ('12',u'BOLETA DE VENTA – COMPROBANTE DE PERCEPCIÓN'),
                ('13',u'GASTO DEDUCIBLE PERSONA NATURAL'),
                ], u'SUNAT Transacción',default="1")
        date_invoice = fields.Date(string='Invoice Date',
                                   readonly=True, states={'draft': [('readonly', False)]}, index=True,
                                   help="Keep empty to use the current date", copy=False, default=datetime.now())
        tipo_nota_credito = fields.Selection([
                ('1',u'ANULACÍON DE LA OPERACIÓN'),
                ('2',u'ANULACÍON POR ERROR EN EL RUC'),
                ('3',u'CORRECCIÓN POR ERROR EN LA DESCRIPCIÓN'),
                ('4',u'DESCUENTO GLOBAL'),
                ('5',u'DESCUENTO POR ÍTEM'),
                ('6',u'DEVOLUCIÓN TOTAL'),
                ('7',u'DEVOLUCIÓN POR ÍTEM'),
                ('8',u'BONIFICACIÓN'),
                ('9',u'DISMINUCIÓN EN EL VALOR'),
                ('10',u'OTROS CONCEPTOS'),], u'Tipo de Nota de Credito', default="1")
        #Datos que retorna sunat
        aceptada_por_sunat=fields.Boolean(default=False)
        sunat_description=fields.Char(string='Estado', readonly=True)
        sunat_responsecode=fields.Char()
        enlace_del_pdf=fields.Char(string='Enlace PDF', readonly=True)

        #????
        @api.multi
        def invoice_validate(self):
                for i in self:
                        moneda = i.account_id.currency_id.name if i.account_id.currency_id.id else 'PEN'
                        if moneda == i.currency_id.name:
                                pass
                        else:
                                raise UserError(
                                        "La moneda de la factura no coincide con la moneda de la cuenta.")
                        # if i.serie_id.id
                        # i.serie_id_internal = i.serie_id.id
                        # i.nro_internal = i.serie_id.sequence_id.next_by_id()#aqui es la cuestion
                        i.reference = i.serie_id.sequence_id.next_by_id()  # aqui es la cuestion
                        print ("referencia actualizada", i.numero)
                        # i.number = i.nro_internal
                        # i.reference =i.nro_internal

                        # i.onchange_suplier_invoice_number_it()
                        # if  i.serie_id.id or i.reference:
                        # i.number = i.reference
                t = super(AccountInvoiceInherit, self).invoice_validate()
                return t
        #??????
        @api.multi
        def reprint(self):
                print ("*****PDF", self.url_pdf)
                webbrowser.open(self.url_pdf)

        @api.multi
        def action_invoice_open(self):
                t = super(AccountInvoiceInherit, self).action_invoice_open()
                if self.serie_id.is_factelec:
                        self.date_invoice = datetime.now((pytz.timezone('America/Lima'))) #asegurarse que la fecha sea la actual
                        data = self.facturacion_electronica()
                        if (data):
                                self.url_pdf = data[1]
                return t
        
        def facturacion_electronica(self):
                company = self[0].env.user.company_id
                nf_id = self.env['credentials.nubefact'].search([('serial_id', '=', self[0].serie_id.id)])
                if not nf_id:
                        #Volviendo numero a su estado actual
                        seq = self.env['ir.sequence'].search([('name', '=', self.serie_id.sequence_id.name)])
                        seq.number_next_actual = self.numero
                        raise UserError(_('No se puede realizar la facturación. \nLa serie seleccionada no tiene credenciales, brindelas en Ventas>Configuracion F.E.'))
                
                if self.type_document_id[0].id == 2: #Factura
                        tipo_doc = 1
                elif self.type_document_id[0].id == 4: #Boleta de Venta
                        tipo_doc = 2
                elif self.type_document_id[0].id == 8: #Nota de Credito
                        tipo_doc = 3
                        factura_origen = self.env['account.invoice'].search([('number', '=', self.origin)])
                        if factura_origen.type_document_id.id == 2:
                                tipo_doc_origen = 1
                        elif factura_origen.type_document_id.id == 4:
                                tipo_doc_origen = 2
                        else:
                                tipo_doc_origen = 0
                elif self.type_document_id[0].id == 9: #Nota de Debito
                        tipo_doc = 4
                else:
                        tipo_doc = 0

                lineas = []
                total_descuento = 0
                for linea in self.invoice_line_ids:
                        tax_percent = 0
                        percent = 0
                        for impuesto in linea.invoice_line_tax_ids:
                                if impuesto.amount_type == 'percent':
                                        percent = percent + impuesto.amount / 100
                                else:
                                        percent = percent + impuesto.amount
                        if not impuesto.id:
                                raise osv.except_osv('Error!', u'No puede crearse Lineas de Factura sin Impuestos')
                        if impuesto.price_include:
                                unit_included = linea.price_unit
                                unit_noincluded = unit_included / (1 + percent)
                        else:
                                unit_included = linea.price_unit * (1 + (impuesto.amount / 100))
                                unit_noincluded = linea.price_unit
                        unit_noincluded = float(
                                decimal.Decimal(str(unit_noincluded)).quantize(decimal.Decimal("1.1111"),
                                                                               decimal.ROUND_HALF_DOWN))
                        descuento = abs(((unit_noincluded * (linea.discount / 100)) * linea.quantity))
                        total_descuento = total_descuento + descuento
                        totalsinimpuetos = linea.price_subtotal
                        imp_igv = linea.price_subtotal * percent

                        tipo_de_igv = 0
                        for impuesto in linea.invoice_line_tax_ids:
                                if impuesto.ebill_tax_type:
                                        tipo_de_igv = impuesto.ebill_tax_type
                        
                        if linea.product_id.type == 'service':
                                umed = "ZZ"
                        else:
                                umed = "NIU"

                        line_unit_val = "%.6f" % abs(unit_included) if impuesto.ebill_tax_type not in ['6', '2', '3',
                                                                                                         '4', '5',
                                                                                                         '7'] else "%.6f" % abs(
                                unit_noincluded)
                        #si se quieren valores diferentes colocar unit_included arriba al final
                        line_unit_price = "%.6f" % abs(unit_noincluded)
                        line_discount = "%.2f" % descuento if descuento != 0 else ""
                        line_subtotal = float(
                                decimal.Decimal(str(abs(totalsinimpuetos))).quantize(decimal.Decimal("1.11"),
                                                                                     decimal.ROUND_HALF_DOWN))
                        line_igv = float(decimal.Decimal(str(abs(imp_igv))).quantize(decimal.Decimal("1.11"),
                                                                                     decimal.ROUND_HALF_DOWN))
                        line_total = float(decimal.Decimal(str(abs(unit_included * linea.quantity))
                                                           ).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN))
                        line_ant_reg = "false"
                        line_ant_doc_serie = ""
                        line_ant_doc_num = ""
                        item = {"unidad_de_medida": umed,
                                "codigo": linea.product_id.default_code if linea.product_id.default_code else "",
                                "descripcion": linea.product_id.name,
                                "cantidad": linea.quantity,
                                "valor_unitario": line_unit_price, #sin igv
                                "precio_unitario": line_unit_val, #con igv
                                "descuento": line_discount,
                                "subtotal": "%.2f" % line_subtotal,
                                "tipo_de_igv": tipo_de_igv,
                                "igv": "%.2f" % line_igv if line_igv else '0.00',
                                "total": "%.2f" % line_total,
                                "anticipo_regularizacion": line_ant_reg,
                                "anticipo_documento_serie": line_ant_doc_serie,
                                "anticipo_documento_numero": line_ant_doc_num,
                                }
                        lineas.append(item)
                
                total_igv = 0
                total_gravada = 0
                for linea in lineas:
                        if linea['anticipo_regularizacion'] == 'true':
                                montobase = float(linea['subtotal']) * -1
                                total_igv = total_igv - float(linea['igv'])
                        else:
                                montobase = float(linea['subtotal'])
                                total_igv = total_igv + float(linea['igv'])
                        if linea['tipo_de_igv'] in ['1']:
                                total_gravada = total_gravada + montobase
                total_gravada_r = abs(float(decimal.Decimal(str(total_gravada)).quantize(
                        decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
                total_igv_r = abs(float(decimal.Decimal(str((total_igv))).quantize(
                        decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
                total_r = abs(float(decimal.Decimal(str((total_gravada + total_igv))
                                                    ).quantize(decimal.Decimal("1.11"), decimal.ROUND_HALF_DOWN)))
                

                jsontext = {
                        "operacion": "generar_comprobante",
                        "tipo_de_comprobante": tipo_doc,
                        "serie": self.serie_id.name,
                        "numero": int(self.numero),
                        "sunat_transaction": int(self.sunat_transaction_type),
                        "cliente_tipo_de_documento": int(self.partner_id.catalog_06_id.code),
                        "cliente_numero_de_documento": self.partner_id.vat,
                        "cliente_denominacion": str(self.partner_id.name),
                        "cliente_direccion": self.partner_id.street if self.partner_id.street else "",
                        "cliente_email": self.partner_id.email if self.partner_id.email else "",
                        "cliente_email_1": "",
                        "cliente_email_2": "",
                        "fecha_de_emision": self.date_invoice,
                        "fecha_de_vencimiento": self.date_due,
                        "moneda": 1,
                        "tipo_de_cambio": "",
                        "porcentaje_de_igv": 18.00,
                        "descuento_global": "",
                        "total_descuento": "%.6f" % total_descuento, #?? if total_descuento != 0 else "",
                        "total_anticipo": "",
                        "total_gravada": "%.2f" % total_gravada_r,
                        "total_inafecta": "",
                        "total_exonerada": "",
                        "total_igv": "%.2f" % total_igv_r,
                        "total_gratuita": "",
                        "total_otros_cargos": "",
                        "total": "%.2f" % total_r,
                        "percepcion_tipo": "",
                        "percepcion_base_imponible": "",
                        "total_percepcion": "",
                        "total_incluido_percepcion": "",
                        "detraccion": 'false',
                        "observaciones": self.comment or '',
                        "documento_que_se_modifica_tipo": 1,
                        "documento_que_se_modifica_serie": factura_origen.serie_id.name if tipo_doc==3 else "",
                        "documento_que_se_modifica_numero": int(factura_origen.numero) if tipo_doc==3 else "",
                        "tipo_de_nota_de_credito": self.tipo_nota_credito,
                        "tipo_de_nota_de_debito": "",
                        "enviar_automaticamente_a_la_sunat": 'true',
                        "enviar_automaticamente_al_cliente": "true" if self.partner_id.email else 'false',
                        "codigo_unico": "",
                        "condiciones_de_pago": self.payment_term_id.name or "",
                        "medio_de_pago": "",
                        "placa_vehiculo": "",
                        "orden_compra_servicio": "",
                        "tabla_personalizada_codigo": "",
                        "formato_de_pdf": "", }
                jsontext.update({'items': lineas})
                '''
                guias = []
                guia={
                                  "guia_tipo": 1,
                                  "guia_serie_numero": "0001-23"
                }
                guias.append(guia)
                jsontext.update({'guias':guias}
                '''

                jsonDoc = json.dumps(jsontext, ensure_ascii=False).encode('utf-8')
                print(jsonDoc)

                try:
                        req = urllib.request.Request(nf_id.url_nubefact)
                        req.add_header('Content-Type', 'application/json')
                        req.add_header('Authorization', 'Token token="'+nf_id.token_nubefact+'"')
                        response = urllib.request.urlopen(req, jsonDoc).read()
                except:
                        #Volviendo numero a su estado actual
                        seq = self.env['ir.sequence'].search([('name', '=', self.serie_id.sequence_id.name)])
                        seq.number_next_actual = self.numero
                        raise osv.except_osv('Error al procesar datos de factura electrónica, verifica tu conexion a internet y tus credenciales')
                
                respuesta = json.loads(response.decode('utf-8'))
                print(">RESPUESTA", respuesta)

                self.aceptada_por_sunat = respuesta['aceptada_por_sunat']
                self.sunat_description = respuesta['sunat_description']
                self.sunat_responsecode = respuesta['sunat_responsecode']
                self.enlace_del_pdf = respuesta['enlace_del_pdf']
                webbrowser.open(self.enlace_del_pdf)
                return (respuesta['codigo_hash'], respuesta['enlace_del_pdf'], respuesta['cadena_para_codigo_qr'])
