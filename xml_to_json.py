import xmltodict
import json
import sys

def convert_xml_to_json(xml_string):
    try:
        xml_dict = xmltodict.parse(xml_string)
        json_string = json.dumps(xml_dict, indent=4)
        return json_string
    except Exception as e:
        return f"Error converting XML to JSON: {e}"

def main():
    xml_data = sys.stdin.read().strip()
    json_result = convert_xml_to_json(xml_data)
    print(json_result)

if __name__ == "__main__":
    main()
