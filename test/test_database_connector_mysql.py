from typing import Dict

import pytest
from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL



@pytest.mark.parametrize(
    'values, condition, expected',
    [
        pytest.param(
            {'some_key': 'some_value',
             'some_other_key': 'some_other_value'},
            'some_condition',
            'UPDATE some_table SET some_key = %s, some_other_key = %s WHERE some_condition',
            id='2_values'
        ),
        pytest.param(
            {'some_key': 'some_value'},
            'some_condition',
            'UPDATE some_table SET some_key = %s WHERE some_condition',
            id='1_value'
        )
    ]
)
def test_prepare_update_query(values: Dict, expected: str, condition: str):
    class A():
        _prepared_statement_placeholder = '%s'

    self = A()
    assert DatabaseConnectorMYSQL._prepare_update_query(self, 'some_table', values,  condition) == expected
