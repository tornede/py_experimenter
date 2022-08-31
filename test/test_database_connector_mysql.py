import pytest

from py_experimenter.database_connector_mysql import DatabaseConnectorMYSQL


@pytest.mark.parametrize(
    'args, modified_args',
    [
        (['a', 'b'], ['a', 'b']),
        ([], []),
        (['a', ], ['a']),
        (['a`b'], ['a``b']),
        (['a``b'], ['a````b']),

    ]
)
def test_escape_sql_chars(args, modified_args):
    assert DatabaseConnectorMYSQL.escape_sql_chars(*args) == modified_args
