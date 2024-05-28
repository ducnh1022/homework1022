import json

class commonConverter:
    # Static variable to hold the template
    TEMPLATE = {
        "Workbook": {
            "data_source": {
                "data_source_name": None,  # To be filled later
                "table_name": "<name_of_table_in_ds>",  # Placeholder
                "unique_script": "unique_script_for_this_data_source"  # Placeholder
            }
        }
    }

    def __init__(self, input_file):
        with open(input_file, 'r') as file:
            self.data = json.load(file)

    def qlik_to_common(self):
        # Initialize the template
        common_format = json.loads(json.dumps(self.TEMPLATE))  # Deep copy of the template
        common_format["Workbook"]["data_source"]["data_source_name"] = self.data["data_sources"][0]

        # Process each sheet
        for sheet_name in self.data["ws_sheets"]:
            common_format["Workbook"][sheet_name] = self.process_sheet(self.data["ws_sheets"][sheet_name])

        return common_format

    def process_sheet(self, sheet_data):
        sheet_objects = {}
        for obj in sheet_data["sheet_objects"]:
            if "chart" in obj["sheet_object_info"]["Type"].lower() or "table" in obj["sheet_object_info"]["Type"].lower():
                object_id = obj["sheet_object_info"]["ObjectId"]
                object_info = self.process_object(obj)
                sheet_objects[object_id] = object_info
        return sheet_objects

    def process_object(self, obj):
        # Extract basic info
        obj_type = obj["sheet_object_info"]["Type"]
        obj_caption = obj["sheet_object_info"].get("Caption", "No Caption")

        # Extract equations
        x_aggregation, x_column = self.extract_equation(obj["dimension"]) if obj["dimension"] else ("", "")
        y_aggregation, y_column = self.extract_equation(obj["expression"]) if obj["expression"] else ("", "")

        return {
            "description": {
                "type": obj_type,
                "title": obj_caption,
                "position": "Add Position Here"  # Placeholder
            },
            "x_equation": {
                "aggregation": x_aggregation,
                "column": x_column
            },
            "y_equation": {
                "aggregation": y_aggregation,
                "column": y_column
            }
        }

    def extract_equation(self, equation_list):
        equation = equation_list[0]["PseudoDef"] if "PseudoDef" in equation_list[0] else equation_list[0]["Definition"]
        return self.parse_equation(equation)
    
    def parse_equation(self, equation):
        parts = equation.split('(')
        func = parts[0].strip('=') if len(parts) > 1 else "None"
        column_name = parts[-1].strip(')')
        return func.lower(), column_name.lower()

# Usage
converter = commonConverter('result-qlik.json')
converted_data = converter.qlik_to_common()

# To save the converted data
with open('common_layer.json', 'w') as f:
    json.dump(converted_data, f, indent=4)
