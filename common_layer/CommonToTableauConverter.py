import json
import xmltodict

# Updated helper dictionaries
FUNCTION_INFO = {
    'count': {'name': 'cnt', 'func_type': 'quantitative'},
    'median': {'name': 'med', 'func_type': 'quantitative'},
    'year': {'name': 'yr', 'func_type': 'ordinal'},
    'sum': {'name': 'sum', 'func_type': 'quantitative'},
    'max': {'name': 'sum', 'func_type': 'quantitative'},
    'none': {'name': 'none', 'func_type': 'ordinal'}
}

CHART_INFO = {
    'Bar Chart': 'Bar',
    'Pivot Table': 'Automatic',
    'Pie Chart': 'Pie'
}

class commonToTableauConverter:
    # Static template for result structure
    RESULT_TEMPLATE = {
        "sheet_info": {
            "Sheet_Id": "",
            "Title": "",
            "ChildObjects": ["pane"]
        },
        "sheet_objects": {
            "pane": {
                "dimensions": {
                    "x_dimension": "",
                    "y_dimension": "",
                    "pane": {
                        "@selection-relaxation-option": "selection-relaxation-allow",
                        "view": {
                            "breakdown": {
                                "@value": "auto"
                            }
                        },
                        "mark": {
                            "@class": ""
                        }
                    }
                },
                "columns": {
                    "@datasource": "",
                    "column-instance": [],
                    "column": []
                }
            }
        }
    }

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path

    def load_input_json(self):
        """Read and return the JSON content from the input file."""
        with open(self.input_path, 'r') as input_file:
            return json.load(input_file)

    def save_json(self, data):
        """Save the result data as a JSON file to the output path."""
        with open(self.output_path, 'w') as output_file:
            json.dump(data, output_file, indent=4)

    def convert_to_xml(self, data):
        """Convert the generated dictionary into an XML string."""
        return xmltodict.unparse(data, pretty=True)

    def find_column_instance(self, data_source, column_name, agg_info):
        """Generate the column-instance entry based on the data source column and function info."""
        column = data_source['columns'].get(column_name)
        if column:
            return {
                "@column": column_name,
                "@derivation": agg_info.get('name', ''),
                "@name": f"[{agg_info.get('name', '')}:{column_name.split('[')[1].split(']')[0]}:qk]",
                "@pivot": "key",
                "@type": agg_info.get('func_type', '')
            }

    def find_columns(self, data_source, column_names):
        """Generate the list of column definitions based on the provided column names and the data source."""
        columns = []
        for column_name in column_names:
            column_info = data_source['columns'].get(column_name)
            if column_info:
                columns.append({
                    "@caption": column_info['name'].strip('[]'),
                    "@datatype": column_info['datatype'],
                    "@name": column_info['name'],
                    "@role": column_info['role'],
                    "@type": column_info['type']
                })
        return columns

    def generate_dimensions(self, data_source_name, column_instances, eq_column):
        """Generate dimensions by matching column instances and appending the data source name."""
        for instance in column_instances:
            if instance["@column"] == eq_column:
                return f"[{data_source_name}].{instance['@name']}"


    def create_chart_entry(self, data_source_name, doc_name, chart_data, data_source):
        """Generate and return a dictionary for a specific chart entry."""
        title = chart_data['description']['title']
        chart_type = chart_data['description']['type']
        chart_class = CHART_INFO.get(chart_type, 'Bar')

        x_eq = chart_data['x_equation']
        y_eq = chart_data['y_equation']

        x_agg_info = FUNCTION_INFO.get(x_eq['aggregation'], {})
        y_agg_info = FUNCTION_INFO.get(y_eq['aggregation'], {})

        column_instances = [
            self.find_column_instance(data_source, f"[{x_eq['column']}]", x_agg_info),
            self.find_column_instance(data_source, f"[{y_eq['column']}]", y_agg_info)
        ]
        column_instances = [ci for ci in column_instances if ci is not None]

        column_names = [f"[{x_eq['column']}]", f"[{y_eq['column']}]"]
        columns = self.find_columns(data_source, column_names)

        # Derive dimensions from column instances
        x_dimension = self.generate_dimensions(data_source_name, column_instances, f"[{x_eq['column']}]")
        y_dimension = self.generate_dimensions(data_source_name, column_instances, f"[{y_eq['column']}]")

        # Create a copy of the static template and populate it with specific values
        chart_entry = json.loads(json.dumps(self.RESULT_TEMPLATE))
        chart_entry["sheet_info"]["Sheet_Id"] = f"{{{doc_name}}}"
        chart_entry["sheet_info"]["Title"] = title
        chart_entry["sheet_objects"]["pane"]["dimensions"]["x_dimension"] = x_dimension
        chart_entry["sheet_objects"]["pane"]["dimensions"]["y_dimension"] = y_dimension
        chart_entry["sheet_objects"]["pane"]["dimensions"]["pane"]["mark"]["@class"] = chart_class
        chart_entry["sheet_objects"]["pane"]["columns"]["@datasource"] = data_source_name
        chart_entry["sheet_objects"]["pane"]["columns"]["column-instance"] = column_instances
        chart_entry["sheet_objects"]["pane"]["columns"]["column"] = columns

        return chart_entry

    def generate_all_charts(self, workbook):
        """Generate a dictionary containing all chart entries."""
        result = {}
        data_source = workbook['data_source']
        data_source_name = data_source['name']

        for doc_name, doc_data in workbook.items():
            if not doc_name.startswith('Document'):
                continue

            for chart_name, chart_data in doc_data.items():
                title = chart_data['description']['title']
                result[title] = self.create_chart_entry(data_source_name, doc_name, chart_data, data_source)

        return result
        
    def transform(self,data):
        transformed_data = {
            "worksheets": {
                "worksheet": []
            }
        }

        # Iterate over each sheet in the input data
        for sheet_name, sheet_content in data.items():
            sheet_info = sheet_content['sheet_info']
            sheet_objects = sheet_content['sheet_objects']['pane']

            worksheet = {
                "@name": sheet_info['Title'],
                "table": {
                    "view": {
                        "datasources": {
                            "datasource": {
                                "@caption": "zydrunas-events (zydrunas-events)",
                                "@name": sheet_objects['columns']['@datasource']
                            }
                        },
                        "datasource-dependencies": {
                            "@datasource": sheet_objects['columns']['@datasource'],
                            "column-instance": [],
                            "column": []
                        },
                        "aggregation": {
                            "@value": "true"
                        }
                    },
                    "style": None,
                    "panes": {
                        "pane": {
                            "@selection-relaxation-option": sheet_objects['dimensions']['pane']['@selection-relaxation-option'],
                            "view": {
                                "breakdown": {
                                    "@value": "auto"
                                }
                            },
                            "mark": {
                                "@class": sheet_objects['dimensions']['pane']['mark']['@class']
                            }
                        }
                    },
                    "rows": sheet_objects['dimensions']['y_dimension'],
                    "cols": sheet_objects['dimensions']['x_dimension'] if 'x_dimension' in sheet_objects['dimensions'] else None
                },
                "simple-id": {
                    "@uuid": sheet_info['Sheet_Id']
                }
            }

            # Process columns and column instances
            for col in sheet_objects['columns']['column']:
                worksheet['table']['view']['datasource-dependencies']['column'].append({
                    "@caption": col.get('@caption', ''),
                    "@datatype": col['@datatype'],
                    "@name": col['@name'],
                    "@role": col['@role'],
                    "@type": col['@type']
                })

            for instance in sheet_objects['columns']['column-instance']:
                worksheet['table']['view']['datasource-dependencies']['column-instance'].append({
                    "@column": instance['@column'],
                    "@derivation": instance['@derivation'],
                    "@name": instance['@name'],
                    "@pivot": instance['@pivot'],
                    "@type": instance['@type']
                })

            transformed_data['worksheets']['worksheet'].append(worksheet)

        return transformed_data

    def convert(self):
        """Main conversion function to read the input JSON and write the result to the output."""
        common_layer = self.load_input_json()
        result = self.generate_all_charts(common_layer['Workbook'])
        result_xml = self.transform(result)

        # Save as JSON
        self.save_json(result_xml)

        # Convert and print as XML (you can also save this to a file)
        output = self.convert_to_xml({"Workbook": result_xml})
        with open('tableau-result.xml', 'w') as result_file:
            result_file.write(output)


# Usage
converter = commonToTableauConverter('common_layer.json', 'result-common-to-tableau.json')
converter.convert()
