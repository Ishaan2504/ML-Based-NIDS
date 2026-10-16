import os
import yaml


def test_config_yaml_structure():
    config_path = os.path.join("config", "config.yaml")
    assert os.path.exists(config_path)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    assert "project" in cfg
    assert "paths" in cfg
    assert "splitting" in cfg
    assert "models" in cfg
    assert cfg["splitting"]["train_ratio"] == 0.60


def test_label_map_yaml_structure():
    label_map_path = os.path.join("config", "label_map.yaml")
    assert os.path.exists(label_map_path)

    with open(label_map_path, "r", encoding="utf-8") as f:
        labels_data = yaml.safe_load(f)

    assert "labels" in labels_data
    assert "BENIGN" in labels_data["labels"]
    assert "DDoS" in labels_data["labels"]
    assert "PortScan" in labels_data["labels"]
