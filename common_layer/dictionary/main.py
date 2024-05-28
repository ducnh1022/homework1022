from config_loader import ConfigLoader
from function import Function
from chart import Chart

# Load configuration from YAML file
config_loader = ConfigLoader('config.yaml')

# Create instances of other classes using the configuration loader
function = Function(config_loader)
chart = Chart(config_loader)

# Usage example
print(function.get_function_info('count'))  # Output: {'name': 'cnt', 'func_type': 'quantitative'}
print(chart.get_chart_info('Bar Chart'))    # Output: 'Bar'
