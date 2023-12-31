from cur.core.strategy import ArchiveStrategy


class TarGzAdapter(ArchiveStrategy):
    def __init__(self, tar_gz_strategy):
        self.tar_gz_strategy = tar_gz_strategy

    def create(self, archive_manager, file_names_or_dir):
        return self.tar_gz_strategy.create(archive_manager, file_names_or_dir)

    def extract(self, archive_manager, extract_path):
        return self.tar_gz_strategy.extract(archive_manager, extract_path)

    def add(self, archive_manager, file_names_or_dir):
        return self.tar_gz_strategy.add(archive_manager, file_names_or_dir)

    def remove(self, archive_manager, items_to_remove):
        return self.tar_gz_strategy.remove(archive_manager, items_to_remove)

    def edit_metadata(self, archive_manager, new_metadata):
        return self.tar_gz_strategy.edit_metadata(archive_manager, new_metadata)

    def show_metadata(self, archive_manager):
        return self.tar_gz_strategy.show_metadata(archive_manager)

    def test(self, archive_manager):
        return self.tar_gz_strategy.test(archive_manager)

class ZipAdapter(ArchiveStrategy):
    def __init__(self, zip_strategy):
        self.zip_strategy = zip_strategy

    def create(self, archive_manager, file_names_or_dir):
        return self.zip_strategy.create(archive_manager, file_names_or_dir)

    def extract(self, archive_manager, extract_path):
        return self.zip_strategy.extract(archive_manager, extract_path)

    def add(self, archive_manager, file_names_or_dir):
        return self.zip_strategy.add(archive_manager, file_names_or_dir)

    def remove(self, archive_manager, items_to_remove):
        return self.zip_strategy.remove(archive_manager, items_to_remove)

    def edit_metadata(self, archive_manager, new_metadata):
        return self.zip_strategy.edit_metadata(archive_manager, new_metadata)

    def show_metadata(self, archive_manager):
        return self.zip_strategy.show_metadata(archive_manager)

    def test(self, archive_manager):
        return self.zip_strategy.test(archive_manager)


class RarAdapter(ArchiveStrategy):
    def __init__(self, rar_strategy):
        self.rar_strategy = rar_strategy

    def create(self, archive_manager, file_names_or_dir):
        return self.rar_strategy.create(archive_manager, file_names_or_dir)

    def extract(self, archive_manager, extract_path):
        return self.rar_strategy.extract(archive_manager, extract_path)

    def add(self, archive_manager, file_names_or_dir):
        return self.rar_strategy.add(archive_manager, file_names_or_dir)

    def remove(self, archive_manager, items_to_remove):
        return self.rar_strategy.remove(archive_manager, items_to_remove)

    def edit_metadata(self, archive_manager, new_metadata):
        return self.rar_strategy.edit_metadata(archive_manager, new_metadata)

    def show_metadata(self, archive_manager):
        return self.rar_strategy.show_metadata(archive_manager)

    def test(self, archive_manager):
        return self.rar_strategy.test(archive_manager)

class AceAdapter(ArchiveStrategy):
    def __init__(self, ace_strategy):
        self.ace_strategy = ace_strategy

    def create(self, archive_manager, file_names_or_dir):
        return self.ace_strategy.create(archive_manager, file_names_or_dir)

    def extract(self, archive_manager, extract_path):
        return self.ace_strategy.extract(archive_manager, extract_path)

    def add(self, archive_manager, file_names_or_dir):
        return self.ace_strategy.add(archive_manager, file_names_or_dir)

    def remove(self, archive_manager, items_to_remove):
        return self.ace_strategy.remove(archive_manager, items_to_remove)

    def edit_metadata(self, archive_manager, new_metadata):
        return self.ace_strategy.edit_metadata(archive_manager, new_metadata)

    def show_metadata(self, archive_manager):
        return self.ace_strategy.show_metadata(archive_manager)

    def test(self, archive_manager):
        return self.ace_strategy.test(archive_manager)