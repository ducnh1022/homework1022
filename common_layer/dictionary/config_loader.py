import yaml

class ConfigLoader:
    def __init__(self, yaml_file):
        self.config = self._load_yaml(yaml_file)

    def _load_yaml(self, yaml_file):
        with open(yaml_file, 'r') as file:
            return yaml.safe_load(file)

    @property
    def function_info(self):
        return self.config.get('function_info', {})

    @property
    def chart_info(self):
        return self.config.get('chart_info', {})
