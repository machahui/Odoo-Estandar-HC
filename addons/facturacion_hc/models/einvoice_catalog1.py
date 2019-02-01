from odoo import models, fields, api

class einvoice_catalog_01(models.Model):
    _name = "einvoice.catalog.01"
    _description = 'Codigo de Tipo de documento'

    code = fields.Char(string='Codigo', size=4, index=True, required=True)
    name = fields.Char(string='Descripcion', size=128, index=True, required=True)
    is_active = fields.Boolean(string='Activo', default=False)

    @api.multi
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for table in self:
            l_name = table.code and table.code + ' - ' or ''
            l_name += table.name
            result.append((table.id, l_name))
        return result

class einvoice_catalog_06(models.Model):
    _name = "einvoice.catalog.06"
    _description = 'Tipo de documento de Identidad'

    code = fields.Char(string='Codigo', size=4, index=True, required=True)
    name = fields.Char(string='Descripcion', size=128, index=True, required=True)
    default = fields.Char(string='Valor por defecto', size=128)

    @api.multi
    @api.depends('code', 'name')
    def name_get(self):
        result = []
        for table in self:
            l_name = table.code and table.code + ' - ' or ''
            l_name += table.name
            result.append((table.id, l_name))
        return result