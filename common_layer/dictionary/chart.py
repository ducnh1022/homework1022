from config_loader import ConfigLoader

class Chart:
    def __init__(self, config_loader):
        self.chart_info = config_loader.chart_info

    def get_chart_info(self, key):
        return self.chart_info.get(key)
