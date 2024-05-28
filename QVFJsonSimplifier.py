import os
import json
import re

class QVFJsonSimplifier:
    # Define constant templates as class variables
    OBJ_TEMPLATE = {
        "sheet_object_info": {
            "ObjectId": None,
            "Caption": None,
            "Type": None
        },
        "dimension": [],
        "expression": []
    }

    SIMPLIFIED_DATA_TEMPLATE = {
        "Document": {
            "sheet_info": {},
            "sheet_objects": []
        }
    }

    def __init__(self):
        self.dimensions_data = None
        self.measures_data = None

    def filter_json_files(self, folder_path):
        files = os.listdir(folder_path)
        return [file for file in files if file.endswith('.json') and 'sheet' in file]

    def simplify_json(self, folder_path):
        folder_path = os.path.join(folder_path, "objects")
        files = [file for file in os.listdir(folder_path) if file.endswith('.json') and 'sheet' in file]
        result = {"ws_sheets": {}, "data_sources": []} 
        for file_name in files:
            with open(os.path.join(folder_path, file_name), 'r') as f:
                data = json.load(f)
                simplified_data = self.simplified_view(data, folder_path)
                result['ws_sheets'][file_name] = simplified_data
                
        self.integrate_datasource(folder_path, result)
        return result
    
    def integrate_datasource(self, folder_path, result):
        script_path = os.path.join(folder_path, "../script.qvs")  # Assuming script.qvs is one level up from the objects folder
        with open(script_path, 'r') as f:
            content = f.read()

        # Regex to extract the last string after "FROM" and before the file extension within square brackets
        matches = re.findall(r"FROM \[.*[\/\\]([^\/\\]+)\.\w+\]", content)
        for match in matches:
            result["data_sources"].append(match)  # Append each found data source name to the result

    def simplified_view(self, data, folder_path):
        # Create a new instance of simplified data from the template
        simplified_data = json.loads(json.dumps(self.SIMPLIFIED_DATA_TEMPLATE))
        self.populate_sheet_info(data, simplified_data)
        self.process_sheet_objects(data, simplified_data, folder_path)
        return simplified_data

    def populate_sheet_info(self, data, simplified_data):
        simplified_data["Document"]["sheet_info"] = {
            "SheetId": data.get("qProperty", {}).get("qInfo", {}).get("qId", ""),
            "Title": data.get("qProperty", {}).get("qMetaDef", {}).get("title", ""),
            "ChildObjects": {"ObjectId": []}
        }

    def process_sheet_objects(self, data, simplified_data, folder_path):
        if "qChildren" in data:
            for child in data["qChildren"]:
                self.process_child(child, simplified_data, folder_path)

    def process_child(self, child, simplified_data, folder_path):
        qInfo = child.get("qProperty", {}).get("qInfo", {})
        objectId = qInfo.get("qId", "")
        simplified_data["Document"]["sheet_info"]["ChildObjects"]["ObjectId"].append(objectId)

        obj = self.get_new_obj(objectId, child.get("qProperty", {}).get("title", ""), qInfo.get("qType", ""))
        hypercube_def = child.get("qProperty", {}).get("qHyperCubeDef", {})
        dimensions = hypercube_def.get("qDimensions", [])
        dimension_ids = [d.get("qLibraryId") for d in dimensions if "qLibraryId" in d]
        measures = hypercube_def.get("qMeasures", [])
        measure_ids = [d.get("qLibraryId") for d in measures if "qLibraryId" in d]
        
        if any(d.get("qLibraryId") for d in dimensions):
            self.integrate_dimensions(obj, folder_path, dimension_ids)
        else:
            self.process_dimension(child, obj)
        if any(m.get("qLibraryId") for m in measures):
            self.integrate_measures(obj, folder_path,measure_ids)
        else:
            self.process_measure(child, obj)

        simplified_data["Document"]["sheet_objects"].append(obj)

    def get_new_obj(self, objectId, caption, obj_type):
        new_obj = json.loads(json.dumps(self.OBJ_TEMPLATE))  # Deep copy the template
        new_obj['sheet_object_info']['ObjectId'] = objectId
        new_obj['sheet_object_info']['Caption'] = caption
        new_obj['sheet_object_info']['Type'] = obj_type
        return new_obj

    def integrate_dimensions(self, obj, folder_path, dimension_ids):
        if not self.dimensions_data:
            dimensions_path = os.path.join(folder_path, 'dimensions.json')
            with open(dimensions_path, 'r') as file:
                self.dimensions_data = json.load(file)
        for dimension in self.dimensions_data:
            for dimension_id in dimension_ids:
                if dimension["qInfo"]["qId"] == dimension_id:
                    obj["dimension"].append({
                        "Definition": dimension["qDim"].get("qFieldDefs", [""]),
                        "Label": dimension["qDim"].get("qFieldLabels", [""]),
                        "LabelExpression": dimension["qDim"].get("qLabelExpression", "")
                    })
            
               
    def integrate_measures(self, obj, folder_path, measure_ids):
        if not self.measures_data:
            measures_path = os.path.join(folder_path, 'measures.json')
            with open(measures_path, 'r') as file:
                self.measures_data = json.load(file)
        for measure in self.measures_data:
            for measure_id in measure_ids:
                if measure["qInfo"]["qId"] == measure_id:
                    obj["expression"].append({
                        "Definition": measure["qMeasure"].get("qDef", ""),
                        "Label": measure["qMeasure"].get("qLabel", ""),
                        "LabelExpression": measure["qMeasure"].get("qLabelExpression", "")
                    })

    def process_dimension(self, child, obj):
        dimensions = child.get("qProperty", {}).get("qHyperCubeDef", {}).get("qDimensions", [])
        for dim in dimensions:
            definition = dim.get("qDef", {}).get("qFieldDefs", [""])[0]
            label = dim.get("qDef", {}).get("qFieldLabels", [""])[0]
            obj["dimension"].append({
                "Definition": definition,
                "Label": label
            })

    def process_measure(self, child, obj):
        measures = child.get("qProperty", {}).get("qHyperCubeDef", {}).get("qMeasures", [])
        for measure in measures:
            definition = measure.get("qDef", {}).get("qDef", "")
            label = measure.get("qDef", {}).get("qLabel", "")
            obj["expression"].append({
                "Definition": definition,
                "Label": label
            })

if __name__ == '__main__':
    folder_path = "E:/download/misc/POC demo/qlik-tableau-migration/qlik-tableau-migration/qlik-charts-with-data-and-script-sameer-poc--unbuild/qlik-charts-with-data-and-script-sameer-poc--unbuild"
    simplifier = QVFJsonSimplifier()

    converted_data = simplifier.simplify_json(folder_path)
    with open(folder_path + 'simplified_view.json', 'w') as fp:
        json.dump(converted_data, fp,indent=4)
    print(json.dumps(converted_data, indent=4))
