class UuidTracker:
    def __init__(self):
        self.old_to_new_uuid_map = {}

    def track(self, old_uuid: str, new_uuid: str):
        self.old_to_new_uuid_map[old_uuid] = new_uuid

    def find_new_uuid(self, old_uuid: str):
        new_uuid = self.old_to_new_uuid_map.get(old_uuid)
        if new_uuid is None:
            raise Exception(f'Could not find new uuid for {old_uuid}')

        return new_uuid