# -*- coding: utf-8 -*-
import os
import flask_mongorest
from flask_mongorest.resources import Resource
from flask_mongorest import operators as ops
from flask_mongorest.methods import *
from flask_mongorest.exceptions import UnknownFieldError
from flask import Blueprint
from mpcontribs.api.core import SwaggerView
from mpcontribs.api.tables.document import Tables
from mpcontribs.api.projects.views import ProjectsResource
from mpcontribs.api.contributions.views import ContributionsResource

templates = os.path.join(os.path.dirname(flask_mongorest.__file__), "templates")
tables = Blueprint("tables", __name__, template_folder=templates)


class TablesResource(Resource):
    document = Tables
    related_resources = {
        "project": ProjectsResource,
        "contribution": ContributionsResource,
    }
    filters = {
        "id": [ops.In, ops.Exact],
        "contribution": [ops.In, ops.Exact],
        "is_public": [ops.Boolean],
        "name": [ops.In, ops.Exact, ops.Contains],
        "columns": [ops.IContains],
    }
    fields = ["id", "contribution", "is_public", "name", "columns"]
    allowed_ordering = ["is_public", "name"]  # TODO data sorting
    paginate = True
    default_limit = 10
    max_limit = 100
    fields_to_paginate = {"data": [20, 1000]}

    @staticmethod
    def get_optional_fields():
        return ["data", "config", "total_data_rows", "total_data_pages"]

    def value_for_field(self, obj, field):
        # add total_data_rows and total_data_pages keys
        if field == "total_data_rows":
            # NOTE get table with full data field to determine totals
            table = Tables.objects.only("data").get(id=obj.id)
            total_data_rows = len(table.data)
            obj.update(set__total_data_rows=total_data_rows)
            return total_data_rows
        elif field == "total_data_pages":
            per_page_default = self.fields_to_paginate["data"][0]
            per_page = int(self.params.get("data_per_page", per_page_default))
            if hasattr(obj, "total_data_rows"):
                total_data_rows = obj.total_data_rows
            else:
                table = Tables.objects.only("total_data_rows").get(id=obj.id)
                if hasattr(table, "total_data_rows"):
                    total_data_rows = table.total_data_rows
                else:
                    total_data_rows = self.value_for_field(obj, "total_data_rows")
            total_data_pages = int(total_data_rows / per_page)
            total_data_pages += bool(total_data_rows % per_page)
            return total_data_pages
        else:
            raise UnknownFieldError


class TablesView(SwaggerView):
    resource = TablesResource
    methods = [Fetch, BulkCreate, Delete, Update, BulkFetch, BulkUpdate]
