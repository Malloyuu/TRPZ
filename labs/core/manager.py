from cur.core.strategy import TarGzStrategy, ZipStrategy, RarStrategy, AceStrategy


class ArchiveManager:
    def __init__(self, archive_type, archive_path):
        self.archive_type = archive_type
        self.archive_path = archive_path
        self.strategy = None

        if archive_type == 'tar.gz':
            self.strategy = TarGzStrategy.get_strategy()
        elif archive_type == 'zip':
            self.strategy = ZipStrategy.get_strategy()
        elif archive_type == 'rar':
            self.strategy = RarStrategy.get_strategy()
        elif archive_type == 'ace':
            self.strategy = AceStrategy.get_strategy()


    def split(self, part_size):
        return self.strategy.split(self, part_size)

    def create(self, file_names_or_dir):
        return self.strategy.create(self, file_names_or_dir)

    def extract(self, extract_path):
        return self.strategy.extract(self, extract_path)

    def add(self, file_names_or_dir):
        return self.strategy.add(self, file_names_or_dir)

    def remove(self, items_to_remove):
        return self.strategy.remove(self, items_to_remove)

    def edit_metadata(self, new_metadata):
        return self.strategy.edit_metadata(self, new_metadata)

    def show_metadata(self):
        return self.strategy.show_metadata(self)

    def test(self):
        return self.strategy.test(self)