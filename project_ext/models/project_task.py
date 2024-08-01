# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Task(models.Model):
    _inherit = 'project.task'

    @api.constrains('parent_id')
    def check_parent_id(self):
        for obj in self:
            this = obj.sudo()
            if this.parent_id:
                this.tag_ids = this.parent_id.tag_ids
                this.project_id = this.parent_id.project_id

    task_member_ids = fields.Many2many('res.users', 'project_user_memeber_rel', 'user_id', 'project_id', string='Project Members',
                                       help="only these memebers can be assigned to this project's tasks", compute="_get_task_members")

    user_ids = fields.Many2many('res.users', relation='project_task_user_rel', column1='task_id',
                                column2='user_id', string='Assignees', context={'active_test': False}, tracking=True
                                # ,domain="[('id', 'in', task_member_ids)]"
                                )
    project_tag_required = fields.Boolean(related='project_id.tag_required')
    plan_start = fields.Datetime(string="Plan Start", tracking=True)
    plan_end = fields.Datetime(string="Plan End", tracking=True)
    actual_start = fields.Datetime(string="Actual Start", tracking=True)
    actual_end = fields.Datetime(string="Actual End", tracking=True)
    date_deadline = fields.Datetime(string='Deadline', index=True, copy=True, tracking=True)
    log_stage_ids = fields.One2many('project.task.log.stage', 'task_id', 'Task History')

    @api.depends('project_id')
    def _get_task_members(self):
        for task in self.sudo():
            task.task_member_ids = task.project_id.user_id | task.project_id.task_member_ids | task.project_id.project_deputy_ids

    @api.constrains('stage_id')
    def check_task_stage(self):
        for record in self:
            if record.stage_id:
                last_stage = self.env['project.task.log.stage'].search([
                    ('end_date', '=', False),
                    ('task_id', '=', record.id)], limit=1, order="end_date desc")
                if last_stage and last_stage.stage_id.id == record.stage_id.id:
                    continue
                last_stage and last_stage.sudo().write({'end_date': datetime.today()})
                record.log_stage_ids.sudo().create({
                    'task_id': record.id,
                    'stage_id': record.stage_id.id,
                    'start_date': datetime.today(),
                })

    def _is_project_accessible(self):
        """
        check if current user has access to the related project
        """
        if self.env.su or self.env.user.has_group('project.group_project_manager'):
            return True
        if not self.task_member_ids:
            return True
        if self.env.user.id in [x.id for x in self.task_member_ids]:
            return True
        return False

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Task, self).create(vals_list)
        [not getattr(obj, 'stage_id') and setattr(obj, 'stage_id', self.env.context.get('default_stage_id'))
         for obj in res]
        return res

    def write(self, vals):
        if not self._is_project_accessible():
            raise UserError(_("You Are not allowed to modify this task."))
        if 'stage_id' in vals and not vals['stage_id']:
            vals.pop('stage_id')
        res = super(Task, self).write(vals)
        return res

    def unlink(self):
        for data in self:
            if not data._is_project_accessible():
                raise UserError(_("You Are Not Allowed To Remove This Task"))
        res = super(Task, self).unlink()
        return res


class TaskLogStage(models.Model):
    _name = 'project.task.log.stage'
    _description = 'Project Task Log Stage'

    task_id = fields.Many2one('project.task', string='Task', readonly=True, ondelete='cascade', index=True,)
    stage_id = fields.Many2one('project.task.type', string='Stage', readonly=True, ondelete='cascade', index=True,)
    start_date = fields.Datetime("Start", readonly=True)
    end_date = fields.Datetime("End", readonly=True)
