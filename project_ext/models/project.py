# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json


logger = logging.getLogger(__name__)


class Project(models.Model):
    _inherit = 'project.project'

    task_member_ids = fields.Many2many('res.users', 'project_user_memeber_rel', 'user_id', 'project_id', string='Project Members',
                                       help="only these memebers can be assigned to this project's tasks")

    project_deputy_ids = fields.Many2many('res.users', 'project_user_deputy_rel', 'user_id', 'project_id', string="PM Deputies",
                                          help="These Group Of People Has The Same Access As Project Manager")
    tag_required = fields.Boolean(string="Tag Required", default=False)
    privacy_visibility = fields.Selection([
        ('followers', 'Invited internal users'),
        ('employees', 'All internal users'),
        ('portal', 'Invited portal users and all internal users'),
    ],
        string='Visibility', required=True,
        default='followers',
        help="People to whom this project and its tasks will be visible.\n\n"
        "- Invited internal users: when following a project, internal users will get access to all of its tasks without distinction. "
        "Otherwise, they will only get access to the specific tasks they are following.\n "
        "A user with the project > administrator access right level can still access this project and its tasks, even if they are not explicitly part of the followers.\n\n"
        "- All internal users: all internal users can access the project and all of its tasks without distinction.\n\n"
        "- Invited portal users and all internal users: all internal users can access the project and all of its tasks without distinction.\n"
        "When following a project, portal users will get access to all of its tasks without distinction. Otherwise, they will only get access to the specific tasks they are following.\n\n"
        "When a project is shared in read-only, the portal user is redirected to their portal. They can view the tasks, but not edit them.\n"
        "When a project is shared in edit, the portal user is redirected to the kanban and list views of the tasks. They can modify a selected number of fields on the tasks.\n\n"
        "In any case, an internal user with no project access rights can still access a task, "
        "provided that they are given the corresponding URL (and that they are part of the followers if the project is private).")

    def _check_is_project_admin(self):
        "check if current user is the admin of the project"
        for obj in self:
            if (self.env.su
                    or self.env.user.has_group('project.group_project_manager')
                    or obj.user_id.id == self.env.user.id
                    or self.env.user.id in list(obj.project_deputy_ids.ids)):
                return True
        raise UserError(_("Only Project Manager and PM Deputies of the project can create the project"))

    def get_project_access(self):
        for obj in self:
            if (self.env.su
                    or self.env.user.has_group('project.group_project_manager')
                    or obj.user_id.id == self.env.user.id
                    or self.env.user.id in list(obj.project_deputy_ids.ids)):
                return True
        return False

    @api.model
    def create(self, vals):
        res = super(Project, self).create(vals)
        [obj._check_is_project_admin() for obj in res]
        self.env.registry.clear_cache()
        return res

    def write(self, vals):
        if len(vals) == 1 and 'sequence' in vals:
            return super(Project, self.sudo()).write(vals)
        [obj._check_is_project_admin() for obj in self]
        res = super(Project, self).write(vals)
        self.env.registry.clear_cache()
        return res

    def unlink(self):
        [obj._check_is_project_admin() for obj in self]
        res = super(Project, self).unlink()
        self.env.registry.clear_cache()
        return res

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        return []

    @api.model
    def insert_directly(self, table, data):
        # self._cr.execute(f'delete from {table}')
        # self._cr.execute(f'''
        #         SELECT pg_catalog.setval(
        #             pg_get_serial_sequence('{table}', 'id'),
        #             COALESCE((SELECT MAX(id) + 1 FROM {table}), 1),
        #             false
        #         )
        #     ''')
        # try:
        cols = ", ".join(data[0].keys())
        qurey = f"INSERT INTO {table} ({cols}) VALUES "
        value = False
        try:
            for item in data:
                if value:
                    qurey += ', '
                validate_data = []
                for k in item.keys():
                    if k in ('name', 'label_tasks', 'description') and table not in ('project_task'):
                        if not item[k]:
                            validate_data.append('NULL')
                        else:
                            item_value = item[k].replace("'", "''")
                            validate_data.append(f"'{json.dumps({'en_US': item_value})}'")
                        # validate_data.append(''' '{"en_US": "%s"}' ''' % item[k])
                    elif isinstance(item[k], int):
                        if item[k]:
                            validate_data.append(f'{item[k]}')
                        else:
                            validate_data.append('NULL')
                    else:

                        if k in ('active', 'display_in_project', 'subject', 'author_guest_id', 'create_uid', 'author_id'):
                            validate_data.append(item[k])
                        elif item[k]:
                            item_value = item[k].replace("'", "''")
                            validate_data.append(f"'{item_value}'")
                        else:
                            validate_data.append('NULL')
                q_values = ", ".join(validate_data)
                value = f"({q_values})"
                qurey += value
            self._cr.execute(qurey)
        finally:
            # APPEND IDENTITY
            self._cr.commit()
            # self._cr.execute(f'ALTER TABLE {table} ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY')
            self._cr.execute(f'''
                SELECT pg_catalog.setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE((SELECT MAX(id) + 1 FROM {table}), 1),
                    false
                )
            ''')
            self._cr.commit()
            return 1

    @api.model
    def isnert_follower(self, res_model, res_ids, partner_ids):
        self.env['mail.followers']._insert_followers(res_model, res_ids, partner_ids)
        return 1

    @api.model
    def update_mail(self, id, value):
        self.env['mail.message'].sudo().browse(id).write(value)
        return 1


class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    @ api.model
    def create(self, vals):
        res = super(ProjectMilestone, self).create(vals)
        [obj.project_id._check_is_project_admin() for obj in res]
        return res

    def write(self, vals):
        res = super(ProjectMilestone, self).write(vals)
        [obj.project_id._check_is_project_admin() for obj in self]
        return res

    def unlink(self):
        [obj.project_id._check_is_project_admin() for obj in self]
        return super(ProjectMilestone, self).unlink()


class ProjectUpdate(models.Model):
    _inherit = 'project.update'

    @ api.model
    def create(self, vals):
        res = super(ProjectUpdate, self).create(vals)
        [obj.project_id._check_is_project_admin() for obj in res]
        return res

    def write(self, vals):
        res = super(ProjectUpdate, self).write(vals)
        [obj.project_id._check_is_project_admin() for obj in self]
        return res

    def unlink(self):
        [obj.project_id._check_is_project_admin() for obj in self]
        return super(ProjectUpdate, self).unlink()


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    @ api.model
    def create(self, vals):
        res = super(ProjectProjectStage, self).create(vals)
        [obj.project_id._check_is_project_admin() for obj in res]
        return res

    def write(self, vals):
        res = super(ProjectProjectStage, self).write(vals)
        [obj.project_id._check_is_project_admin() for obj in self]
        return res

    def unlink(self):
        [obj.project_id._check_is_project_admin() for obj in self]
        return super(ProjectProjectStage, self).unlink()


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    @ api.model
    def create(self, vals):
        res = super(ProjectTaskType, self).create(vals)
        [project._check_is_project_admin() for project in res.project_ids]
        return res

    def write(self, vals):
        res = super(ProjectTaskType, self).write(vals)
        [project._check_is_project_admin() for project in self.project_ids]
        return res

    def unlink(self):
        [project._check_is_project_admin() for project in self.project_ids]
        return super(ProjectTaskType, self).unlink()
