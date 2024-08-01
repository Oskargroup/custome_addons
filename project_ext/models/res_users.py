# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date
from odoo import models, fields, api


class Users(models.Model):
    _inherit = 'res.users'

    def _get_can_remove_members(self):
        access = False
        if self._context.get('project_id'):
            project = self.env['project.project'].browse(self._context['project_id'])
            access = self.env.user.id in [*project.project_deputy_ids.ids, project.user_id.id] or self.env.is_admin()
        [setattr(record, 'can_remove_members', access) for record in self]

    def remove_task_member(self):
        if self._context.get('project_id'):
            self.env['project.project'].browse(self._context['project_id']).write({
                'task_member_ids': [(3, self.id)]
            })

    can_remove_members = fields.Boolean(compute="_get_can_remove_members", string="remove members")
