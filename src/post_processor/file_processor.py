import copy
import os
from abc import abstractmethod
from shutil import copyfile


from post_processor.file import File, JsonFile
from post_processor.util import uuid5, get_key, set_key
from post_processor.uuid_tracker import UuidTracker


ZERO_TIMESTAMP = '2021-01-01T00:00:00.000000Z'

SCHEMA_PROD_URL = 'https://schema.humancellatlas.org/'
SCHEMA_STAGING_URL = 'https://schema.staging.data.humancellatlas.org/'


class FileProcessor:
    def __init__(self, project_dir_path: str, new_dir_path: str, uuid_tracker: UuidTracker):
        self.project_dir_path = project_dir_path
        self.new_dir_path = new_dir_path
        self.uuid_tracker = uuid_tracker
        self.project_dir_name = os.path.basename(os.path.normpath(project_dir_path))

    def get_new_dir_path(self, dir_path):
        new_project_dir_path = os.path.join(self.new_dir_path, self.project_dir_name)
        new_dir_path = dir_path.replace(self.project_dir_path, new_project_dir_path)
        return new_dir_path

    @abstractmethod
    def process(self, file: File):
        raise NotImplementedError


class DataProcessor(FileProcessor):
    def process(self, entity_file: File):
        new_dir_path = self.get_new_dir_path(entity_file.dir_path)
        new_file_path = os.path.join(new_dir_path, entity_file.filename)
        os.makedirs(new_dir_path, exist_ok=True)
        copyfile(entity_file.file_path, new_file_path)


class JsonFileProcessor(FileProcessor):
    @abstractmethod
    def process(self, file: JsonFile):
        raise NotImplementedError

    def replace_described_by(self, new_content):
        described_by = get_key('describedBy', new_content)
        new_described_by = described_by.replace(SCHEMA_PROD_URL, SCHEMA_STAGING_URL)
        set_key(new_content, 'describedBy', new_described_by)
        return new_content


class MetadataProcessor(JsonFileProcessor):
    def process(self, json_file: JsonFile):
        schema_type = json_file.content.get('schema_type')

        if schema_type not in ['project', 'biomaterial', 'process', 'protocol', 'file']:
            raise Exception(f'Invalid schema type: {schema_type}')

        new_uuid = uuid5(json_file.metadata_id)

        self.update_metadata_file(json_file, new_uuid)
        self.uuid_tracker.track(json_file.entity_uuid, json_file.new_entity_uuid)

    def update_metadata_file(self, json_file: JsonFile, new_uuid: str):
        json_file.new_entity_uuid = new_uuid

        new_filename = self.replace_uuid_and_version_in_filename(json_file)
        new_content = self.replace_uuid_and_version_in_content(json_file)
        new_content = self.replace_described_by(new_content)
        new_dir_path = self.get_new_dir_path(json_file.dir_path)
        new_file_path = os.path.join(new_dir_path, new_filename)

        json_file.new_content = new_content
        json_file.new_dir_path = new_dir_path
        json_file.new_file_path = new_file_path

    def replace_uuid_and_version_in_filename(self, json_file: JsonFile):
        new_filename = json_file.filename.replace(json_file.entity_uuid, json_file.new_entity_uuid)
        new_filename = new_filename.replace(json_file.version, ZERO_TIMESTAMP)
        return new_filename

    def replace_uuid_and_version_in_content(self, json_file: JsonFile):
        new_content = copy.deepcopy(json_file.content)
        set_key(new_content, 'provenance.document_id', json_file.new_entity_uuid)
        set_key(new_content, 'provenance.submission_date', ZERO_TIMESTAMP)
        set_key(new_content, 'provenance.update_date', ZERO_TIMESTAMP)
        return new_content


class DescriptorProcessor(JsonFileProcessor):
    def process(self, entity_file: JsonFile):
        new_uuid = self.uuid_tracker.find_new_uuid(entity_file.entity_uuid)

        new_content = self.replace_uuid_and_version_in_content(entity_file.content)

        new_filename = entity_file.filename.replace(entity_file.entity_uuid, new_uuid)
        new_filename = new_filename.replace(entity_file.version, ZERO_TIMESTAMP)

        new_dir_path = self.get_new_dir_path(entity_file.dir_path)
        new_file_path = os.path.join(new_dir_path, new_filename)

        entity_file.new_content = new_content
        entity_file.new_dir_path = new_dir_path
        entity_file.new_file_path = new_file_path

    def replace_uuid_and_version_in_content(self, content: dict) -> dict:
        new_content = copy.deepcopy(content)
        # This is from dataFileUuid in file metadata document
        old_file_uuid = new_content['file_id']
        filename = new_content['file_name']
        # TODO Should we get the uuid from filename?
        # This means it will always be the same with file metadata uuid
        new_file_uuid = uuid5(filename)
        new_content['file_id'] = new_file_uuid
        new_content['file_version'] = ZERO_TIMESTAMP
        self.replace_described_by(new_content)
        return new_content


class LinkProcessor(JsonFileProcessor):
    def process(self, entity_file: JsonFile):
        new_content = self.replace_uuids_in_content(entity_file.content)
        new_filename = self.replace_uuid_and_version_in_filename(entity_file)
        new_dir_path = self.get_new_dir_path(entity_file.dir_path)
        new_file_path = os.path.join(new_dir_path, new_filename)

        entity_file.new_content = new_content
        entity_file.new_dir_path = new_dir_path
        entity_file.new_file_path = new_file_path

    def replace_uuids_in_content(self, content: dict):
        new_content = copy.deepcopy(content)
        self.replace_described_by(new_content)
        for link in new_content.get('links', []):
            if link.get('link_type') == 'process_link':
                self.replace_uuids_in_process_link(link)
            if link.get('link_type') == 'supplementary_file_link':
                self.replace_uuids_in_supplementary_file_link(link)

        return new_content

    def replace_uuids_in_process_link(self, link):
        for input in link.get('inputs'):
            old_input_uuid = input['input_id']
            new_input_uuid = self.uuid_tracker.find_new_uuid(old_input_uuid)
            input['input_id'] = new_input_uuid
        for output in link.get('outputs'):
            old_output_uuid = output['output_id']
            new_output_uuid = self.uuid_tracker.find_new_uuid(old_output_uuid)
            output['output_id'] = new_output_uuid
        for protocol in link.get('protocols'):
            old_protocol_id = protocol['protocol_id']
            new_protocol_id = self.uuid_tracker.find_new_uuid(old_protocol_id)
            protocol['protocol_id'] = new_protocol_id

        self.replace_process_uuid(link)

    def replace_process_uuid(self, link):
        old_process_uuid = link['process_id']
        uuid_from_process_id = self.uuid_tracker.find_new_uuid(old_process_uuid)
        new_process_uuid = self.determine_process_uuid(link)
        link['process_id'] = new_process_uuid
        self.uuid_tracker.track(uuid_from_process_id, new_process_uuid)

    def determine_process_uuid(self, link):
        input_ids = [input['input_id'] for input in link.get('inputs')]
        output_ids = [output['output_id'] for output in link.get('outputs')]
        protocol_ids = [protocol['protocol_id'] for protocol in link.get('protocols')]

        input_ids.sort()
        output_ids.sort()
        protocol_ids.sort()

        merge_ids = '|I|' + ','.join(input_ids) + '|P|' + ','.join(output_ids) + '|O|' + ','.join(protocol_ids)
        new_process_uuid = uuid5(merge_ids)

        return new_process_uuid

    def replace_uuids_in_supplementary_file_link(self, link):
        entity = link.get('entity')
        old_entity_uuid = entity['entity_id']
        new_entity_uuid = self.uuid_tracker.find_new_uuid(old_entity_uuid)
        entity['entity_id'] = new_entity_uuid
        for file in link.get('files'):
            old_file_uuid = file.get('file_id')
            new_file_uuid = self.uuid_tracker.find_new_uuid(old_file_uuid)
            file['file_id'] = new_file_uuid

    def replace_uuid_and_version_in_filename(self, entity_file: JsonFile):
        new_process_uuid = self.find_new_process_uuid(entity_file.entity_uuid)
        new_project_uuid = self.uuid_tracker.find_new_uuid(entity_file.project_uuid)

        new_filename = entity_file.filename.replace(entity_file.entity_uuid, new_process_uuid)
        new_filename = new_filename.replace(entity_file.project_uuid, new_project_uuid)
        new_filename = new_filename.replace(entity_file.version, ZERO_TIMESTAMP)
        return new_filename

    def find_new_process_uuid(self, old_process_uuid):
        uuid_from_process_id = self.uuid_tracker.find_new_uuid(old_process_uuid)
        uuid_from_all_ids = self.uuid_tracker.find_new_uuid(uuid_from_process_id)
        return uuid_from_all_ids


class ProcessMetadataProcessor(MetadataProcessor):
    def process(self, json_file: JsonFile):
        uuid_from_process_id = uuid5(json_file.metadata_id)
        new_uuid = self.uuid_tracker.find_new_uuid(uuid_from_process_id)
        self.update_metadata_file(json_file, new_uuid)
        self.replace_process_ids(json_file)

    def replace_process_ids(self, json_file: JsonFile):
        new_content = copy.deepcopy(json_file.new_content)
        json_file.new_content = set_key(new_content, 'process_core.process_id', 'dummy_process')

