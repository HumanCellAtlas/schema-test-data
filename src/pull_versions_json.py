"""
Small script. Imports versions.json from metadata-schema repository (integration branch), processes and compares
with current versions.json in this schema
"""

from copy import deepcopy

import requests as rq
import json
import os




BRANCH = os.environ.get("BRANCH_VERSIONS_JSON", "integration")
COMPONENT_VERSIONS = [
                        "schema_versions",
                        "ebi_schema_versions",
                        "importer_schema_versions",
                        "tdr_schema_versions",
                        "azul_schema_versions",
                        "browser_schema_versions",
                        "pipelines_schema_versions"
                      ]
ROOT_PATH = "/".join(os.path.realpath(__file__).split("/")[:-2])


class VersionsJson:

    def __init__(self):
        self.log = []
        self.versions_url = f"https://raw.githubusercontent.com/HumanCellAtlas/metadata-schema/{BRANCH}/json_schema/versions.json"
        self.pre_processed_versions = self._get_versions_json()
        self.processed_versions = self._process_versions()

    def _get_versions_json(self):
        versions = rq.get(self.versions_url)
        versions.raise_for_status()
        return versions.json()

    def _process_versions(self, from_scratch=False):
        if not os.path.isfile(f"{ROOT_PATH}/versions.json"):
            from_scratch = True

        if from_scratch:
            self.log.append(f"versions.json not found in the root folder {ROOT_PATH}. Proceeding to process from scratch...")
            processed_json = deepcopy(self.pre_processed_versions)
            processed_json['schema_versions'] = {}
            for component in COMPONENT_VERSIONS:
                processed_json['schema_versions'][component] = deepcopy(self.pre_processed_versions['version_numbers'])
            del processed_json['version_numbers']
        else:
            self.log.append(f"versions.json found in the root folder {ROOT_PATH}. Proceeding to process...")
            with open(f"{ROOT_PATH}/versions.json", "r") as f:
                processed_json = json.load(f)

            processed_json['latest_update'] = self.pre_processed_versions['last_update_date']
            for component in COMPONENT_VERSIONS[:2]:
                processed_json[component] = deepcopy(self.pre_processed_versions['version_numbers'])

        self.log.append("Processed successfully!")
        return processed_json

    def write_json(self, path, json_file):
        self.log.append(f"Proceeding to write to '{path}'")
        with open(path, "w") as f:
            json.dump(json_file, f, indent=4, separators=(",", ":"))

    def print_log(self):
        print("\n".join(self.log))

def main():
    versions = VersionsJson()
    versions.write_json(f"{ROOT_PATH}/versions.json", versions.processed_versions)
    versions.log.append("Successfully imported latest versions.json. Exiting...")
    versions.print_log()


if __name__ == "__main__":
    main()

