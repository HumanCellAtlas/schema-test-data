import argparse
import os

from typing import List

from post_processor.file import JsonFile, File
from post_processor.file_processor import MetadataProcessor, DescriptorProcessor, LinkProcessor, \
    ProcessMetadataProcessor, DataProcessor, JsonFileProcessor
from post_processor.util import get_json_file_paths, get_file_paths, dump_json
from post_processor.uuid_tracker import UuidTracker


class PostProcessor:
    def __init__(self, project_dir_path: str, new_dir_path: str = None):
        self.project_dir_path = project_dir_path
        self.new_dir_path = os.getcwd() if not new_dir_path else new_dir_path
        self.uuid_tracker = UuidTracker()

        self.processed_files_by_file_path = {}

    def process(self):
        self.process_json_files(f'{self.project_dir_path}/metadata',
                                MetadataProcessor(self.project_dir_path, self.new_dir_path, self.uuid_tracker))
        self.process_json_files(f'{self.project_dir_path}/descriptors',
                                DescriptorProcessor(self.project_dir_path, self.new_dir_path, self.uuid_tracker))
        self.process_json_files(f'{self.project_dir_path}/links',
                                LinkProcessor(self.project_dir_path, self.new_dir_path, self.uuid_tracker))
        self.process_json_files(f'{self.project_dir_path}/metadata/process',
                                ProcessMetadataProcessor(self.project_dir_path, self.new_dir_path, self.uuid_tracker))

        self.save_files()

        self.process_data_files(f'{self.project_dir_path}/data',
                                DataProcessor(self.project_dir_path, self.new_dir_path, self.uuid_tracker))

    def process_json_files(self, dir_path: str, processor: JsonFileProcessor):
        json_files = self.find_json_files(dir_path)
        for json_file in json_files:
            processor.process(json_file)
            self.processed_files_by_file_path[json_file.file_path] = json_file

    def find_json_files(self, dir_path: str) -> List['JsonFile']:
        entity_files = (JsonFile(file_path) for file_path in get_json_file_paths(dir_path))
        return entity_files

    def save_files(self):
        for file_path in self.processed_files_by_file_path:
            file: JsonFile = self.processed_files_by_file_path.get(file_path)
            os.makedirs(file.new_dir_path, exist_ok=True)
            dump_json(file.new_content, file.new_file_path)

    def process_data_files(self, dir_path: str, processor: DataProcessor):
        entity_files = self.find_data_files(dir_path)
        for entity_file in entity_files:
            processor.process(entity_file)

    def find_data_files(self, dir_path: str) -> List['File']:
        entity_files = (File(file_path) for file_path in get_file_paths(dir_path))
        return entity_files


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
