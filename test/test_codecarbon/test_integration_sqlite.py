import random
import tempfile

import numpy as np
import pytest

from py_experimenter.experimenter import PyExperimenter
from py_experimenter.result_processor import ResultProcessor


@pytest.fixture
def experimenter():
    content = """
    [PY_EXPERIMENTER]
    provider = sqlite 
    database = py_experimenter
    table = integration_test_mysql 

    keyfields = dataset, cross_validation_splits:int, seed:int, kernel
    dataset = iris
    cross_validation_splits = 5
    seed = 2:6:2 
    kernel = linear, poly, rbf, sigmoid

    resultfields = pipeline:LONGTEXT, train_f1:DECIMAL, train_accuracy:DECIMAL, test_f1:DECIMAL, test_accuracy:DECIMAL
    resultfields.timestamps = false

    [CUSTOM] 
    path = sample_data
    """

    # Create temporary experiment configuration file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(content)
        experiment_configuration = f.name

    return PyExperimenter(experiment_configuration)


def run_ml(parameters: dict, result_processor: ResultProcessor, custom_config: dict):
    seed = parameters['seed']
    random.seed(seed)
    np.random.seed(seed)
    
    if parameters['dataset'] != 'iris':
        raise ValueError("Example error")
    #without a small sleep the test fails on windows
    import time
    time.sleep(1)


def test_integration(experimenter: PyExperimenter):
    experimenter.delete_table()
    experimenter.fill_table_from_config()
    experimenter.execute(run_ml, -1)
    table = experimenter.get_codecarbon_table()
    assert list(table.columns) == [
        'ID', 'experiment_id', 'codecarbon_timestamp', 'project_name', 'run_id',
        'duration_seconds', 'emissions_kg', 'emissions_rate_kg_sec', 'cpu_power_watt', 'gpu_power_watt', 'ram_power_watt',
        'cpu_energy_kw', 'gpu_energy_kw', 'ram_energy_kw', 'energy_consumed_kw', 'country_name',
        'country_iso_code', 'region', 'cloud_provider', 'cloud_region', 'os', 'python_version',
        'codecarbon_version', 'cpu_count', 'cpu_model', 'gpu_count', 'gpu_model',
        'longitude', 'latitude', 'ram_total_size', 'tracking_mode', 'on_cloud', 'offline_mode']
    assert table.shape == (12, 33)
    assert list(table['experiment_id']) == [1,2,3,4,5,6,7,8,9,10,11,12]
    
