from cur.core.manager import ArchiveManager


class ArchiveFacade:
    def __init__(self, archive_type, archive_path):
        self.archive_manager = ArchiveManager(archive_type, archive_path)

    def create_archive(self, file_names_or_dir):
        return self.archive_manager.create(file_names_or_dir)

    def extract_archive(self, extract_path):
        return self.archive_manager.extract(extract_path)

    def add_files(self, file_names_or_dir):
        return self.archive_manager.add(file_names_or_dir)

    def remove_items(self, items_to_remove):
        return self.archive_manager.remove(items_to_remove)

    def edit_metadata(self, new_metadata):
        return self.archive_manager.edit_metadata(new_metadata)

    def show_metadata(self):
        return self.archive_manager.show_metadata()

    def test_archive(self):
        return self.archive_manager.test()

    def split_archive(self, part_size):
        return self.archive_manager.split(part_size)