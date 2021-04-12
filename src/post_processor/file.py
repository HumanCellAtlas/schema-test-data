import os

from post_processor.util import get_key, load_json

METADATA_ID_KEY_BY_TYPE = {
    'project': 'project_core.project_short_name',
    'biomaterial': 'biomaterial_core.biomaterial_id',
    'process': 'process_core.process_id',
    'protocol': 'protocol_core.protocol_id',
    'file': 'file_core.file_name',
}


class File:
    def __init__(self, file_path):
        self.file_path = file_path
        self.dir_path, self.filename = os.path.split(file_path)


class JsonFile(File):
    def __init__(self, file_path):
        self.file_path = file_path
        self.dir_path, self.filename = os.path.split(file_path)
        self.project_uuid = None
        self.entity_uuid = None
        self.version = None

        filename_parts = self.filename.split('_')
        filename_parts_len = len(filename_parts)

        if filename_parts_len == 2:
            self.entity_uuid = filename_parts[0]
            self.version = filename_parts[1].replace('.json', '')
        elif filename_parts_len == 3:
            self.entity_uuid = filename_parts[0]
            self.version = filename_parts[1]
            self.project_uuid = filename_parts[2].replace('.json', '')

        self._content = None

        self.new_content = None
        self.new_file_path = None
        self.new_dir_path = None
        self.new_entity_uuid = None

    @property
    def content(self):
        if self._content:
            return self._content

        self._content = load_json(self.file_path)
        return self._content

    @property
    def metadata_id(self):
        schema_type = self.content.get('schema_type')
        id_key = METADATA_ID_KEY_BY_TYPE.get(schema_type)
        return get_key(id_key, self.content)

