# -*- coding: utf-8 -*-
##############################################################################
#
#    OdooDevelopers.
#    Copyright (C) 2017-TODAY OdooDevelopers(<http://www.odoodevelopers.com>).
#    Author: Redouane ADADI(<http://www.odoodevelopers.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _


class CreateUserFromEmployee(models.Model):
    _inherit = 'hr.employee'

    user_check_tick = fields.Boolean('User Check Tick')

    @api.one
    def create_users(self):
        user_id = self.env['res.users'].create({'name': self.name, 'login': self.work_email})
        self.address_home_id = user_id.partner_id.id
        user_id.write({'share': False})
        self.user_id=user_id
        self.user_check_tick = True

    @api.onchange('address_home_id')
    def user_checking(self):
        if self.address_home_id:
            self.user_check_tick = True
        else:
            self.user_check_tick = False
