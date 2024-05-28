import xml.etree.ElementTree as ET
import json

class CommonToTableauDatasource:
    def __init__(self, common_layer_path, datasource_path):
        self.common_layer_path = common_layer_path
        self.datasource_path = datasource_path
        self.common_layer = self.load_json(common_layer_path)
        self.datasource_xml = self.load_xml(datasource_path)
        self.datasource_info = {}
        self.columns = {}

    def load_json(self, path):
        with open(path, 'r') as file:
            return json.load(file)

    def load_xml(self, path):
        with open(path, 'r') as file:
            return file.read()

    def parse_datasource_xml(self):
        try:
            root = ET.fromstring(self.datasource_xml)
            for datasource in root.findall('.//datasource'):
                self.datasource_info['name'] = datasource.get('name')
                self.datasource_info['caption'] = datasource.get('caption')
            for column in root.findall(".//column"):
                role = column.get('role')
                type_ = column.get('type')
                if role and type_:
                    self.columns[column.get('name')] = {
                        'datatype': column.get('datatype'),
                        'name': column.get('name'),
                        'role': role,
                        'type': type_
                    }
        except ET.ParseError:
            raise ValueError("Invalid XML data")

    def update_common_layer(self):
        # Assuming the location to insert XML data is in the 'data_source' section of common_layer
        data_source_section = self.common_layer['Workbook']['data_source']
        data_source_section.update(self.datasource_info)
        data_source_section['columns'] = self.columns
        self.save_updated_json()

    def save_updated_json(self):
        with open(self.common_layer_path, 'w') as file:
            json.dump(self.common_layer, file, indent=4)

    def run_conversion(self):
        self.parse_datasource_xml()
        self.update_common_layer()

# Example usage
converter = CommonToTableauDatasource('common_layer.json', 'input-data-source.txt')
converter.run_conversion()
