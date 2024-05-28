from config_loader import ConfigLoader

class Function:
    def __init__(self, config_loader):
        self.function_info = config_loader.function_info

    def get_function_info(self, key):
        return self.function_info.get(key)
