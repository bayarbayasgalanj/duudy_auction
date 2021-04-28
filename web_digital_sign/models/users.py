# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class Users(models.Model):
    _inherit = 'res.users'

    digital_signature = fields.Binary(string='Signature')
    digital_signature_from_file = fields.Binary(string='Signature from File')

    @api.onchange('digital_signature_from_file')
    def onch_digital_signature_from_file(self):
        if self.digital_signature_from_file:
            self.digital_signature = self.digital_signature_from_file
            self.digital_signature_from_file = False