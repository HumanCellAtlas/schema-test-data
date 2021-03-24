import argparse
import copy
import json
import os
import uuid
from collections import namedtuple
from os import walk
from shutil import copyfile
from typing import List

METADATA_ID_KEY_BY_TYPE = {
    'project': 'project_core.project_short_name',
    'biomaterial': 'biomaterial_core.biomaterial_id',
    'process': 'process_core.process_id',
    'protocol': 'protocol_core.protocol_id',
    'file': 'file_core.file_name',
}

ZERO_TIMESTAMP = '2021-01-01T00:00:00.000000Z'

SCHEMA_PROD_URL = 'https://schema.humancellatlas.org/'
SCHEMA_STAGING_URL = 'https://schema.staging.data.humancellatlas.org/'


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
    return content


def load_json(file_path: str):
    with open(file_path, 'r') as infile:
        content = json.load(infile)
    return content


def dump_json(content: dict, file_path: str):
    with open(file_path, 'w') as outfile:
        json.dump(content, outfile, indent=4, sort_keys=True)


class PostProcessor:
    def __init__(self, project_dir_path: str, new_dir_path: str = None):
        self.project_dir_path = project_dir_path
        self.project_dir_name = os.path.basename(os.path.normpath(project_dir_path))
        self.old_to_new_uuid_map = {}
        self.new_dir_path = os.getcwd() if not new_dir_path else new_dir_path

    def process(self):
        self.process_metadata(f'{self.project_dir_path}/metadata')
        self.process_descriptors(f'{self.project_dir_path}/descriptors')
        self.process_links(f'{self.project_dir_path}/links')
        self.copy_files(f'{self.project_dir_path}/data')

    def process_metadata(self, dir_path: str):
        json_file_paths = self.get_json_file_paths(dir_path)
        for file_path in json_file_paths:
            self.process_a_metadata_file(file_path)

    def process_descriptors(self, dir_path: str):
        for file_path in self.get_json_file_paths(dir_path):
            self.process_descriptor(file_path)

    def process_links(self, dir_path: str):
        for file_path in self.get_json_file_paths(dir_path):
            self.process_link(file_path)

    def copy_files(self, dir_path: str):
        file_paths = self.get_file_paths(dir_path)
        for file_path in file_paths:
            dir_path, filename = os.path.split(file_path)
            new_dir_path = self.get_new_dir_path(dir_path)
            new_file_path = os.path.join(new_dir_path, filename)
            os.makedirs(new_dir_path, exist_ok=True)
            copyfile(file_path, new_file_path)

    def get_json_file_paths(self, dir_path: str):
        file_paths = self.get_file_paths(dir_path)
        json_file_paths = (file_path for file_path in file_paths if '.json' in file_path)
        return json_file_paths

    def get_file_paths(self, dir_path: str) -> List[str]:
        filepaths = []
        for (dirpath, dirnames, filenames) in walk(dir_path):
            for file in filenames:
                full_path = os.path.join(dirpath, file)
                filepaths.append(full_path)
        return filepaths

    def process_a_metadata_file(self, file_path: str):
        dir_path, filename = os.path.split(file_path)

        old_content = load_json(file_path)
        schema_type = old_content.get('schema_type')

        if schema_type not in ['project', 'biomaterial', 'process', 'protocol', 'file']:
            raise Exception(f'Invalid schema type: {schema_type}')

        metadata_id = self.get_metadata_id(old_content)
        new_uuid = str(self.determine_uuid(metadata_id))

        new_filename = self.replace_metadata_filename(filename, new_uuid)
        new_content = self.replace_metadata_file_content(old_content, new_uuid)

        new_dir_path = self.get_new_dir_path(dir_path)
        new_file_path = os.path.join(new_dir_path, new_filename)
        os.makedirs(new_dir_path, exist_ok=True)
        dump_json(new_content, new_file_path)

    def process_link(self, file_path):
        dir_path, filename = os.path.split(file_path)

        new_filename = self.replace_link_filename(filename)

        old_content = load_json(file_path)
        new_content = self.replace_uuids_in_links(old_content)

        new_dir_path = self.get_new_dir_path(dir_path)
        new_file_path = os.path.join(new_dir_path, new_filename)
        os.makedirs(new_dir_path, exist_ok=True)
        dump_json(new_content, new_file_path)

    def process_descriptor(self, file_path):
        dir_path, filename = os.path.split(file_path)

        old_content = load_json(file_path)

        filename_info = self.get_filename_info(filename)
        old_uuid = filename_info.entity_uuid
        old_version = filename_info.version

        new_uuid = self.old_to_new_uuid_map.get(old_uuid)

        new_filename = filename.replace(old_uuid, new_uuid)
        new_filename = new_filename.replace(old_version, ZERO_TIMESTAMP)

        new_content = self.replace_uuid_version_in_descriptor(old_content)
        new_dir_path = self.get_new_dir_path(dir_path)
        new_file_path = os.path.join(new_dir_path, new_filename)
        os.makedirs(new_dir_path, exist_ok=True)
        dump_json(new_content, new_file_path)

    def replace_metadata_filename(self, filename, new_uuid):
        filename_info = self.get_filename_info(filename)
        old_uuid = filename_info.entity_uuid
        old_version = filename_info.version
        self.old_to_new_uuid_map[old_uuid] = new_uuid
        new_filename = filename.replace(old_uuid, new_uuid)
        new_filename = new_filename.replace(old_version, ZERO_TIMESTAMP)
        return new_filename

    def get_filename_info(self, filename):
        FileNameInfo = namedtuple('Filename', 'entity_uuid version project_uuid')

        filename_parts = filename.split('_')
        filename_parts_len = len(filename_parts)

        if filename_parts_len == 2:
            entity_uuid = filename_parts[0]
            version = filename_parts[1].replace('.json', '')
            filename_info = FileNameInfo(entity_uuid, version, None)
        elif filename_parts_len == 3:
            entity_uuid = filename_parts[0]
            version = filename_parts[1]
            project_uuid = filename_parts[2].replace('.json', '')
            filename_info = FileNameInfo(entity_uuid, version, project_uuid)

        return filename_info

    def replace_link_filename(self, filename):
        filename_info = self.get_filename_info(filename)
        old_uuid = filename_info.entity_uuid
        old_version = filename_info.version
        project_uuid = filename_info.project_uuid
        new_uuid = self.old_to_new_uuid_map.get(old_uuid)
        new_project_uuid = self.old_to_new_uuid_map.get(project_uuid)
        new_filename = filename.replace(old_uuid, new_uuid)
        new_filename = new_filename.replace(project_uuid, new_project_uuid)
        new_filename = new_filename.replace(old_version, ZERO_TIMESTAMP)
        return new_filename

    def replace_metadata_file_content(self, old_content, new_uuid):
        new_content = copy.deepcopy(old_content)
        set_key(new_content, 'provenance.document_id', new_uuid)
        set_key(new_content, 'provenance.submission_date', ZERO_TIMESTAMP)
        set_key(new_content, 'provenance.update_date', ZERO_TIMESTAMP)
        self.replace_described_by(new_content)
        return new_content

    def replace_uuid_version_in_descriptor(self, content: dict) -> dict:
        new_content = copy.deepcopy(content)
        # This is from dataFileUuid in file metadata document
        old_file_uuid = new_content['file_id']
        filename = new_content['file_name']
        # TODO Should we get the uuid from filename?
        # This means it will always be the same with metadata uuid
        new_file_uuid = str(self.determine_uuid(filename))
        new_content['file_id'] = new_file_uuid
        new_content['file_version'] = ZERO_TIMESTAMP
        self.replace_described_by(new_content)
        return new_content

    def replace_uuids_in_links(self, content: dict):
        new_content = copy.deepcopy(content)
        self.replace_described_by(new_content)
        for link in new_content.get('links', []):
            if link.get('link_type') == 'process_link':
                old_process_uuid = link['process_id']
                new_process_uuid = self.find_new_uuid(old_process_uuid)
                link['process_id'] = new_process_uuid

                for input in link.get('inputs'):
                    old_input_uuid = input['input_id']
                    new_input_uuid = self.find_new_uuid(old_input_uuid)
                    input['input_id'] = new_input_uuid

                for output in link.get('outputs'):
                    old_output_uuid = output['output_id']
                    new_output_uuid = self.find_new_uuid(old_output_uuid)
                    output['output_id'] = new_output_uuid

                for protocol in link.get('protocols'):
                    old_protocol_id = protocol['protocol_id']
                    new_protocol_id = self.find_new_uuid(old_protocol_id)
                    output['protocol_id'] = new_protocol_id

            if link.get('link_type') == 'supplementary_file_link':
                entity = link.get('entity')
                old_entity_uuid = entity['entity_id']
                new_entity_uuid = self.find_new_uuid(old_entity_uuid)
                entity['entity_id'] = new_entity_uuid
                for file in link.get('files'):
                    old_file_uuid = file.get('file_id')
                    new_file_uuid = self.find_new_uuid(old_file_uuid)
                    file['file_id'] = new_file_uuid

        return new_content

    def replace_described_by(self, new_content):
        described_by = get_key('describedBy', new_content)
        new_described_by = described_by.replace(SCHEMA_PROD_URL, SCHEMA_STAGING_URL)
        set_key(new_content, 'describedBy', new_described_by)

    def get_metadata_id(self, content):
        schema_type = content.get('schema_type')
        id_key = METADATA_ID_KEY_BY_TYPE.get(schema_type)
        return get_key(id_key, content)

    def get_new_dir_path(self, dir_path):
        new_project_dir_path = os.path.join(self.new_dir_path, self.project_dir_name)
        new_dir_path = dir_path.replace(self.project_dir_path, new_project_dir_path)
        return new_dir_path

    def determine_uuid(self, name):
        # TODO can we use this namespace?
        return uuid.uuid5(uuid.NAMESPACE_DNS, name)

    def find_new_uuid(self, old_uuid: str):
        new_uuid = self.old_to_new_uuid_map.get(old_uuid)
        if new_uuid is None:
            raise Exception(f'Could not find new uuid for {old_uuid}')
        return new_uuid


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('path', help="Project directory path", metavar="FILE")
    args = parser.parse_args()

    if "~" in args.path:
        path = os.path.expanduser(args.path)
    else:
        path = args.path

    post_processor = PostProcessor(path)
    post_processor.process()
