import json
import os
import uuid
from typing import List

# doesn't work if path is in list
def get_key(path: str, nested_dict: dict) -> str:
    if path is None:
        raise Exception('path is none')
    sub_paths = path.split('.')
    content = nested_dict

    for sub_path in sub_paths:
        content = content.get(sub_path)
        if content is None:
            return None

    return content


def set_key(nested_dict: dict, path: str, value):
    sub_paths = path.split('.')
    last_key = sub_paths.pop()

    content = nested_dict
    for sub_path in sub_paths:
        content = content.get(sub_path)

    content[last_key] = value
    return nested_dict


def load_json(file_path: str) -> dict:
    with open(file_path, 'r') as infile:
        content = json.load(infile)
    return content


def dump_json(content: dict, file_path: str):
    with open(file_path, 'w') as outfile:
        json.dump(content, outfile, indent=4, sort_keys=True)
        outfile.write("\n")


def uuid5(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))


def get_file_paths(dir_path: str) -> List[str]:
    file_paths = []
    for (dirpath, dirnames, filenames) in os.walk(dir_path):
        for file in filenames:
            full_path = os.path.join(dirpath, file)
            file_paths.append(full_path)
    return file_paths


def get_json_file_paths(dir_path: str):
    file_paths = get_file_paths(dir_path)
    json_file_paths = (file_path for file_path in file_paths if '.json' in file_path)
    return json_file_paths

