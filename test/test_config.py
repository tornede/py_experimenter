import logging

import omegaconf
import pytest

from py_experimenter.config import (
    CodeCarbonCfg,
    CustomCfg,
    DatabaseCfg,
    Keyfield,
    PyExperimenterCfg,
)


@pytest.fixture
def config_file():
    return omegaconf.OmegaConf.load("test/yml_configs/test_config.yml")


def verify_database_config(database_config):
    assert database_config.provider == "sqlite"
    assert database_config.database_name == "py_experimenter"
    assert database_config.table_name == "test_table_sqlite"
    assert isinstance(database_config.keyfields, dict)
    assert database_config.keyfields == {
        "datasetName": Keyfield("datasetName", "VARCHAR(255)", ["A", "B"]),
        "internal_performance_measure": Keyfield("internal_performance_measure", "VARCHAR(255)", ["X", "Z"]),
        "featureObjectiveMeasure": Keyfield("featureObjectiveMeasure", "VARCHAR(255)", ["M"]),
        "seed": Keyfield("seed", "INT", [1, 2]),
        "range_values": Keyfield("range_values", "int", [0, 1, 2, 3, 4]),
    }
    assert database_config.result_timestamps == True
    assert database_config.resultfields == {
        "final_pipeline": "LONGTEXT",
        "final_pipeline_timestamp": "VARCHAR(255)",
        "internal_performance": "FLOAT",
        "internal_performance_timestamp": "VARCHAR(255)",
        "performance_asymmetric_loss": "FLOAT",
        "performance_asymmetric_loss_timestamp": "VARCHAR(255)",
    }


def test_database_config(config_file):
    logger = logging.getLogger(__name__)
    database_config = DatabaseCfg.extract_config(config_file, logger)
    verify_database_config(database_config)


def verify_custom_config(custom_config):
    assert isinstance(custom_config, CustomCfg)
    assert custom_config.custom_values == {"datapath": "path/to/data"}


def test_extract_custom_config(config_file):
    custom_config = CustomCfg.extract_config(config_file, logging.getLogger(__name__))
    verify_custom_config(custom_config)


def verify_codecarbon_config(codecarbon_config):
    assert isinstance(codecarbon_config, CodeCarbonCfg)
    assert codecarbon_config.config == {
        "offline_mode": False,
        "measure_power_secs": 15,
        "tracking_mode": "machine",
        "log_level": "error",
        "save_to_file": True,
        "output_dir": "output/CodeCarbon",
    }


def test_codecarbon_config(config_file):
    codecarbon_config = CodeCarbonCfg.extract_config(config_file, logging.getLogger(__name__))
    verify_codecarbon_config(codecarbon_config)


def test_pyexperimenter_cfg():
    config_path = "test/yml_configs/test_config.yml"
    config = PyExperimenterCfg.extract_config(config_path, logger=logging.getLogger(__name__))
    assert isinstance(config, PyExperimenterCfg)
    assert config.n_jobs == 5

    verify_database_config(config.database_configuration)
    verify_custom_config(config.custom_configuration)
    verify_codecarbon_config(config.codecarbon_configuration)
