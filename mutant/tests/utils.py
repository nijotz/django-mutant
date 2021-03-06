from __future__ import unicode_literals

from django.db import connections
from django.test.testcases import _deferredSkip

from mutant.db.models import MutableModel
from mutant.models.model import ModelDefinition
from mutant.test.testcases import ModelDefinitionDDLTestCase
from mutant.utils import allow_migrate


def table_columns_iterator(db, table_name):
    connection = connections[db]
    cursor = connection.cursor()
    description = connection.introspection.get_table_description(cursor, table_name)
    return (row[0] for row in description)


class BaseModelDefinitionTestCase(ModelDefinitionDDLTestCase):
    def setUp(self):
        self.model_def = ModelDefinition.objects.create(
            app_label='app',
            object_name='Model'
        )

    def assertTableExists(self, db, table):
        tables = connections[db].introspection.table_names()
        msg = "Table '%s.%s' doesn't exist, existing tables are %s"
        self.assertTrue(table in tables, msg % (db, table, tables))

    def assertTableDoesntExists(self, db, table):
        self.assertRaises(AssertionError, self.assertTableExists, db, table)

    def assertModelTablesExist(self, model):
        table = model._meta.db_table
        for db in allow_migrate(model):
            self.assertTableExists(db, table)

    def assertModelTablesDontExist(self, model):
        table = model._meta.db_table
        for db in allow_migrate(model):
            self.assertTableDoesntExists(db, table)

    def assertColumnExists(self, db, table, column):
        columns = tuple(table_columns_iterator(db, table))
        data = {
            'db': db,
            'table': table,
            'column': column,
            'columns': columns
        }
        self.assertIn(column, columns,
                      "Column '%(db)s.%(table)s.%(column)s' doesn't exist, "
                      "%(db)s.'%(table)s's columns are %(columns)s" % data)

    def assertColumnDoesntExists(self, db, table, column):
        self.assertRaises(
            AssertionError, self.assertColumnExists, db, table, column
        )

    def assertModelTablesColumnExists(self, model, column):
        table = model._meta.db_table
        for db in allow_migrate(model):
            self.assertColumnExists(db, table, column)

    def assertModelTablesColumnDoesntExists(self, model, column):
        table = model._meta.db_table
        for db in allow_migrate(model):
            self.assertColumnDoesntExists(db, table, column)


def skipIfMutantModelDBFeature(feature, default=False):
    dbs = tuple(allow_migrate(MutableModel))

    def _dbs_have_feature():
        return all(getattr(connections[db].features, feature, default)
                   for db in dbs)
    return _deferredSkip(_dbs_have_feature,
                         "Databases %s have feature %s" % (dbs, feature))


def skipUnlessMutantModelDBFeature(feature, default=True):
    dbs = tuple(allow_migrate(MutableModel))

    def _dbs_dont_have_feature():
        return all(not getattr(connections[db].features, feature, default)
                   for db in dbs)
    return _deferredSkip(_dbs_dont_have_feature,
                         "Databases %s don't have feature %s" % (dbs, feature))
