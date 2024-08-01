# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError
from odoo.addons.rating.models.rating_data import RATING_LIMIT_MIN, RATING_TEXT

import logging


logger = logging.getLogger(__name__)


class ReportProjectTaskUser(models.Model):
    _inherit = 'report.project.task.user'

    stage_name = fields.Char(size=128, string='Stage Name', required=True)

    def _select(self):
        select_to_append = """,
                tt.name->>'en_US' as stage_name
        """

        return super(ReportProjectTaskUser, self)._select() + select_to_append

    def _group_by(self):
        group_by_to_append = """,
                tt.name
        """
        return super(ReportProjectTaskUser, self)._group_by() + group_by_to_append

    def _from(self):
        from_to_append = f"""
                    LEFT JOIN project_task_type tt ON tt.id = t.stage_id
        """
        return super(ReportProjectTaskUser, self)._from() + from_to_append
