# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OracleResPartner(models.Model):
    _inherit = 'res.partner'


    doctor = fields.Boolean('Doctor')
    doctor_code = fields.Char('Doctor Code')
    ldm_contract_ids = fields.Many2many('ldm.contract', string='Contracts')
    center = fields.Boolean('Center')
    center_code = fields.Char('Center Code')
    patient_age = fields.Char("Age")
    card_number = fields.Char('Card Number')
    patient_number = fields.Char('Patient Number')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], default='male')
    is_public_audience = fields.Boolean()
    separated_invoices = fields.Boolean("Separated Invoices")
    lab2lab = fields.Boolean("Lab to Lab")
    contact_type = fields.Selection([
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('both', 'Both'),
        ('contact', 'Contact')
    ], srting='Contact Type')

    @api.onchange('doctor')
    def compute_doctor_code(self):
        for rec in self:
            if not rec.doctor:
                rec.doctor_code = False
