import os
import subprocess
import tarfile
import zipfile
from abc import ABC, abstractmethod

from cur.core.checksum import ChecksumManager


class ArchiveStrategy(ABC):
    _strategy_instance = None

    @classmethod
    def get_strategy(cls):
        if cls._strategy_instance is None:
            cls._strategy_instance = cls()
        return cls._strategy_instance

    @abstractmethod
    def create(self, archive_manager, file_names_or_dir):
        pass

    @abstractmethod
    def extract(self, archive_manager, extract_path):
        pass

    @abstractmethod
    def add(self, archive_manager, file_names_or_dir):
        pass

    @abstractmethod
    def remove(self, archive_manager, items_to_remove):
        pass

    @abstractmethod
    def edit_metadata(self, archive_manager, new_metadata):
        pass

    @abstractmethod
    def show_metadata(self, archive_manager):
        pass

    @abstractmethod
    def test(self, archive_manager):
        pass

class TarGzStrategy(ArchiveStrategy):
    def create(self, archive_manager, file_names_or_dir):
        if not archive_manager.archive_path.endswith(".tar.gz"):
            archive_manager.archive_path += ".tar.gz"

        try:
            with tarfile.open(archive_manager.archive_path, "w:gz") as tar:
                for item in file_names_or_dir:
                    if os.path.isfile(item):
                        tar.add(item, arcname=os.path.basename(item))
                    elif os.path.isdir(item):
                        for root, dirs, files in os.walk(item):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, item)
                                tar.add(file_path, arcname=arcname)

            checksums = ChecksumManager.calculate(file_names_or_dir)
            checksum_file = f"{archive_manager.archive_path}.checksums.txt"
            ChecksumManager.save(checksums, checksum_file)
            checksum_file = f"{archive_manager.archive_path}.checksums.txt"

            return f"\033[32mChecksums saved to {checksum_file}.\nArchive {archive_manager.archive_path} created successfully.\033[0m"
        except Exception as e:
            return f"\033[31mError creating TAR.GZ archive: {e}\033[0m"

    def split(self, archive_manager, part_size):
        if not archive_manager.archive_path.endswith(".tar.gz"):
            return "\033[31mInvalid archive type. Expected TAR.GZ archive.\033[0m"

        try:
            archive_size = os.path.getsize(archive_manager.archive_path)
            num_parts = -(-archive_size // part_size)  # округление вверх

            with open(archive_manager.archive_path, 'rb') as f:
                for i in range(num_parts):
                    with open(f"{archive_manager.archive_path}.part{i + 1}", 'wb') as part_file:
                        part_file.write(f.read(part_size))

            return f"\033[32mArchive split into {num_parts} parts successfully.\033[0m"
        except Exception as e:
            return f"\033[31mError splitting TAR.GZ archive: {e}\033[0m"

    def extract(self, archive_manager, extract_path):
        messages = []
        try:
            if not archive_manager.archive_path.endswith(".tar.gz"):
                return "\033[31mInvalid archive type. Expected TAR.GZ archive.\033[0m"

            with tarfile.open(archive_manager.archive_path, "r:gz") as tar:
                tar.extractall(path=extract_path)

            checksum_file = f"{archive_manager.archive_path}.checksums.txt"
            if os.path.exists(checksum_file):
                if not ChecksumManager.verify(extract_path, checksum_file):
                    messages.append(
                        "\033[31mChecksum verification failed. The extracted files may be corrupted.\033[0m")
                else:
                    messages.append("\033[32mChecksum verification successful.\033[0m")
            else:
                messages.append("\033[33mNo checksum file found. Skipping verification.\033[0m")

            messages.append(f"Archive extracted to {extract_path}.")
            return '\n'.join(messages)
        except Exception as e:
            return f"\033[31mError extracting TAR.GZ archive: {e}\033[0m"

    def add(self, archive_manager, file_names_or_dir):
        try:
            if not archive_manager.archive_path.endswith(".tar.gz"):
                return "\033[31mInvalid archive type. Expected TAR.GZ archive.\033[0m"

            temp_archive = archive_manager.archive_path + '.temp'
            with tarfile.open(temp_archive, "w:gz") as new_tar:
                with tarfile.open(archive_manager.archive_path, "r:gz") as existing_tar:
                    for member in existing_tar.getmembers():
                        new_tar.addfile(member, existing_tar.extractfile(member.name))

                for item in file_names_or_dir:
                    if os.path.isfile(item):
                        new_tar.add(item, arcname=os.path.basename(item))
                    elif os.path.isdir(item):
                        for root, dirs, files in os.walk(item):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, item)
                                new_tar.add(file_path, arcname=arcname)

            os.remove(archive_manager.archive_path)
            os.rename(temp_archive, archive_manager.archive_path)

            return f"\033[32mFiles added to {archive_manager.archive_path} successfully.\033[0m"
        except Exception as e:
            return f"\033[31mError adding files to TAR.GZ archive: {e}\033[0m"

    def remove(self, archive_manager, items_to_remove):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".tar.gz"):
                result_message += "\033[31mInvalid archive type. Expected TAR.GZ archive.\033[0m\n"
                return result_message

            temp_archive = archive_manager.archive_path + '.temp'
            with tarfile.open(temp_archive, "w:gz") as new_tar:
                with tarfile.open(archive_manager.archive_path, "r:gz") as existing_tar:
                    for member in existing_tar.getmembers():
                        if not any(
                                member.name.startswith(item + '/') or member.name == item for item in items_to_remove):
                            new_tar.addfile(member, existing_tar.extractfile(member.name))

            os.remove(archive_manager.archive_path)
            os.rename(temp_archive, archive_manager.archive_path)

            result_message += f"\033[32mItems removed from {archive_manager.archive_path} successfully.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError removing items from TAR.GZ archive: {e}\033[0m\n"

        return result_message

    def edit_metadata(self, archive_manager, new_metadata):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".tar.gz"):
                result_message += "\033[31mInvalid archive type. Expected TAR.GZ archive.\033[0m\n"
                return result_message

            metadata_file_name = os.path.basename(archive_manager.archive_path) + "_metadata.txt"
            temp_archive_path = archive_manager.archive_path + ".temp"

            with open(metadata_file_name, "w") as metadata_file:
                metadata_file.write(new_metadata)

            with tarfile.open(temp_archive_path, "w:gz") as new_tar:
                with tarfile.open(archive_manager.archive_path, "r:gz") as old_tar:
                    for member in old_tar.getmembers():
                        if member.name != metadata_file_name:
                            new_tar.addfile(member, old_tar.extractfile(member.name))

                new_tar.add(metadata_file_name, arcname=os.path.basename(metadata_file_name))

            os.remove(archive_manager.archive_path)
            os.rename(temp_archive_path, archive_manager.archive_path)
            os.remove(metadata_file_name)

            result_message += f"\033[32mMetadata updated for {archive_manager.archive_path}.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError editing metadata for TAR.GZ archive: {e}\033[0m\n"

        return result_message

    def show_metadata(self, archive_manager):
        result_message = ""
        try:
            if not archive_manager.archive_path.endswith(".tar.gz"):
                result_message += "\033[31mInvalid archive type. Expected TAR.GZ archive.\033[0m\n"
                return result_message

            metadata_file_name = os.path.basename(archive_manager.archive_path) + "_metadata.txt"
            with tarfile.open(archive_manager.archive_path, "r:gz") as tar:
                if metadata_file_name in tar.getnames():
                    member = tar.getmember(metadata_file_name)
                    with tar.extractfile(member) as metadata_file:
                        metadata_content = metadata_file.read().decode('utf-8')
                        result_message += f"\033[32mTAR.GZ Metadata:\n{metadata_content}\033[0m\n"
                else:
                    result_message += "\033[33mNo metadata file found in this TAR.GZ archive.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError showing metadata for {archive_manager.archive_path}: {e}\033[0m\n"

        return result_message

    def test(self, archive_manager):
        result_message = ""
        try:
            if not archive_manager.archive_path.endswith(".tar.gz"):
                result_message += "\033[31mInvalid archive type. Expected TAR.GZ archive.\033[0m\n"
                return result_message

            with tarfile.open(archive_manager.archive_path, "r:gz") as tar:
                tar.getmembers()

            result_message += f"\033[32mTAR.GZ Archive {archive_manager.archive_path} is valid and has no errors.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError testing {archive_manager.archive_path}: {e}\033[0m\n"

        return result_message


class ZipStrategy(ArchiveStrategy):
    def create(self, archive_manager, file_names_or_dir):
        result_message = ""

        if not archive_manager.archive_path.endswith(".zip"):
            archive_manager.archive_path += ".zip"

        try:
            with zipfile.ZipFile(archive_manager.archive_path, 'w') as zipf:
                for item in file_names_or_dir:
                    if os.path.isfile(item):
                        zipf.write(item, arcname=os.path.basename(item))
                    elif os.path.isdir(item):
                        for root, dirs, files in os.walk(item):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, item)
                                zipf.write(file_path, arcname=arcname)

            checksums = ChecksumManager.calculate(file_names_or_dir)
            checksum_file = f"{archive_manager.archive_path}.checksums.txt"
            ChecksumManager.save(checksums, checksum_file)

            result_message += f"\033[32mChecksums saved to {checksum_file}.\n"
            result_message += f"Archive {archive_manager.archive_path} created successfully.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError creating ZIP archive: {e}\033[0m\n"

        return result_message

    def split(self, archive_manager, part_size):
        if not archive_manager.archive_path.endswith(".zip"):
            return "\033[31mInvalid archive type. Expected ZIP archive.\033[0m"

        try:
            archive_size = os.path.getsize(archive_manager.archive_path)
            num_parts = -(-archive_size // part_size)

            with open(archive_manager.archive_path, 'rb') as f:
                for i in range(num_parts):
                    with open(f"{archive_manager.archive_path}.part{i + 1}", 'wb') as part_file:
                        part_file.write(f.read(part_size))

            return f"\033[32mArchive split into {num_parts} parts successfully.\033[0m"
        except Exception as e:
            return f"\033[31mError splitting ZIP archive: {e}\033[0m"

    def extract(self, archive_manager, extract_path):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".zip"):
                result_message += "\033[31mInvalid archive type. Expected ZIP archive.\033[0m\n"
                return result_message

            with zipfile.ZipFile(archive_manager.archive_path, 'r') as zipf:
                zipf.extractall(path=extract_path)

            checksum_file = f"{archive_manager.archive_path}.checksums.txt"
            if os.path.exists(checksum_file):
                if ChecksumManager.verify(extract_path, checksum_file):
                    result_message += "\033[32mChecksum verification successful.\033[0m\n"
                else:
                    result_message += "\033[31mChecksum verification failed. The extracted files may be corrupted.\033[0m\n"
            else:
                result_message += "\033[33mNo checksum file found. Skipping verification.\033[0m\n"

            result_message += f"Archive extracted to {extract_path}.\n"
        except Exception as e:
            result_message += f"\033[31mError extracting ZIP archive: {e}\033[0m\n"

        return result_message

    def add(self, archive_manager, file_names_or_dir):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".zip"):
                result_message += "\033[31mInvalid archive type. Expected ZIP archive.\033[0m\n"
                return result_message

            with zipfile.ZipFile(archive_manager.archive_path, 'a') as zipf:
                for item in file_names_or_dir:
                    if os.path.isfile(item):
                        zipf.write(item, arcname=os.path.basename(item))
                    elif os.path.isdir(item):
                        for root, dirs, files in os.walk(item):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, item)
                                zipf.write(file_path, arcname=arcname)

            result_message += "\033[32mFiles added to {archive_manager.archive_path} successfully.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError adding files to ZIP archive: {e}\033[0m\n"

        return result_message

    def remove(self, archive_manager, items_to_remove):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".zip"):
                result_message += "\033[31mInvalid archive type. Expected ZIP archive.\033[0m\n"
                return result_message

            temp_archive = archive_manager.archive_path + '.temp'
            with zipfile.ZipFile(archive_manager.archive_path, 'r') as existing_zip:
                with zipfile.ZipFile(temp_archive, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:
                    for file_info in existing_zip.infolist():
                        if not any(file_info.filename.startswith(item + '/') or file_info.filename == item for item in
                                   items_to_remove):
                            with existing_zip.open(file_info) as source:
                                new_zip.writestr(file_info, source.read())

            os.remove(archive_manager.archive_path)
            os.rename(temp_archive, archive_manager.archive_path)

            result_message += "\033[32mItems removed from {archive_manager.archive_path} successfully.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError removing items from ZIP archive: {e}\033[0m\n"

        return result_message

    def edit_metadata(self, archive_manager, new_metadata):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".zip"):
                result_message += "\033[31mInvalid archive type. Expected ZIP archive.\033[0m\n"
                return result_message

            with zipfile.ZipFile(archive_manager.archive_path, 'a') as zipf:
                zipf.comment = new_metadata.encode('utf-8')

            result_message += "\033[32mMetadata updated for {archive_manager.archive_path}.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError editing metadata for ZIP archive: {e}\033[0m\n"

        return result_message

    def show_metadata(self, archive_manager):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".zip"):
                result_message += "\033[31mInvalid archive type. Expected ZIP archive.\033[0m\n"
                return result_message

            with zipfile.ZipFile(archive_manager.archive_path, 'r') as zipf:
                comment = zipf.comment.decode('utf-8')
                result_message += f"\033[32mZIP Archive Comment:\n{comment}\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError showing metadata for {archive_manager.archive_path}: {e}\033[0m\n"

        return result_message

    def test(self, archive_manager):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".zip"):
                result_message += "\033[31mInvalid archive type. Expected ZIP archive.\033[0m\n"
                return result_message

            with zipfile.ZipFile(archive_manager.archive_path, 'r') as zipf:
                bad_file = zipf.testzip()
                if bad_file:
                    result_message += f"\033[31mZIP Archive {archive_manager.archive_path} contains a corrupt file: {bad_file}\033[0m\n"
                else:
                    result_message += f"\033[32mZIP Archive {archive_manager.archive_path} is valid and has no errors.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError testing {archive_manager.archive_path}: {e}\033[0m\n"

        return result_message


class RarStrategy(ArchiveStrategy):
    def create(self, archive_manager, file_names_or_dir):
        result_message = ""

        if not archive_manager.archive_path.endswith(".rar"):
            archive_manager.archive_path += ".rar"

        try:
            rar_path = r"C:\Program Files\WinRAR\rar.exe"  # Укажите путь к исполняемому файлу RAR
            args = [rar_path, 'a', archive_manager.archive_path]
            for file_name in file_names_or_dir:
                rel_path = os.path.relpath(file_name, os.path.dirname(archive_manager.archive_path))
                args.append(rel_path)
            subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            result_message += f"\033[32mRAR Archive {archive_manager.archive_path} created successfully.\033[0m\n"

            checksums = ChecksumManager.calculate(file_names_or_dir)
            checksum_file = f"{archive_manager.archive_path}.checksums.txt"
            ChecksumManager.save(checksums, checksum_file)
            result_message += f"\033[32mChecksums saved to {checksum_file}.\033[0m\n"

        except Exception as e:
            result_message += f"\033[31mError creating RAR archive: {e}\033[0m\n"

        return result_message

    def split(self, archive_manager, part_size):
        result_message = ""

        if not archive_manager.archive_path.endswith(".rar"):
            result_message += "\033[31mInvalid archive type. Expected RAR archive.\033[0m\n"
            return result_message

        try:
            archive_size = os.path.getsize(archive_manager.archive_path)
            num_parts = -(-archive_size // part_size)

            with open(archive_manager.archive_path, 'rb') as f:
                for i in range(num_parts):
                    with open(f"{archive_manager.archive_path}.part{i + 1}", 'wb') as part_file:
                        part_file.write(f.read(part_size))

            result_message += f"\033[32mArchive split into {num_parts} parts successfully.\033[0m\n"
        except Exception as e:
            result_message += f"\033[31mError splitting RAR archive: {e}\033[0m\n"

        return result_message

    def extract(self, archive_manager, extract_path):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".rar"):
                result_message += "\033[31mInvalid archive type. Expected RAR archive.\033[0m\n"
                return result_message

            unrar_path = r"C:\Program Files\WinRAR\unrar.exe"  # Укажите путь к исполняемому файлу unrar
            args = [unrar_path, 'x', archive_manager.archive_path, extract_path]
            subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            result_message += f"\033[32mRAR Archive {archive_manager.archive_path} extracted successfully.\033[0m\n"

            checksum_file = f"{archive_manager.archive_path}.checksums.txt"
            if os.path.exists(checksum_file):
                if ChecksumManager.verify(extract_path, checksum_file):
                    result_message += "\033[32mChecksum verification successful.\033[0m\n"
                else:
                    result_message += "\033[31mChecksum verification failed. The extracted files may be corrupted.\033[0m\n"
            else:
                result_message += "\033[31mNo checksum file found. Skipping verification.\033[0m\n"

        except Exception as e:
            result_message += f"\033[31mError extracting RAR archive: {e}\033[0m\n"

        return result_message

    def add(self, archive_manager, file_names_or_dir):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".rar"):
                result_message += "\033[31mInvalid archive type. Expected RAR archive.\033[0m\n"
                return result_message

            rar_path = r"C:\Program Files\WinRAR\rar.exe"
            args = [rar_path, 'a', archive_manager.archive_path]
            for file_name in file_names_or_dir:
                rel_path = os.path.relpath(file_name, os.path.dirname(archive_manager.archive_path))
                args.append(rel_path)
            subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            result_message += f"\033[32mFiles added to {archive_manager.archive_path} successfully.\033[0m\n"

        except Exception as e:
            result_message += f"\033[31mError adding files to RAR archive: {e}\033[0m\n"

        return result_message

    def remove(self, archive_manager, items_to_remove):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".rar"):
                result_message += "\033[31mInvalid archive type. Expected RAR archive.\033[0m\n"
                return result_message

            unrar_path = r"C:\Program Files\WinRAR\unrar.exe"
            for item in items_to_remove:
                subprocess.run([unrar_path, 'd', archive_manager.archive_path, item],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            result_message += f"\033[32mItems removed from {archive_manager.archive_path} successfully.\033[0m\n"

        except Exception as e:
            result_message += f"\033[31mError removing items from RAR archive: {e}\033[0m\n"

        return result_message

    def edit_metadata(self, archive_manager, new_metadata):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".rar"):
                result_message += "\033[31mInvalid archive type. Expected RAR archive.\033[0m\n"
                return result_message

            rar_path = r"C:\Program Files\WinRAR\Rar.exe"
            comment_file_path = archive_manager.archive_path + ".txt"
            try:
                with open(comment_file_path, "w") as comment_file:
                    comment_file.write(new_metadata)
                subprocess.run([rar_path, 'c', '-z' + comment_file_path, archive_manager.archive_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                result_message += f"\033[32mMetadata updated for {archive_manager.archive_path}.\033[0m\n"
            finally:
                if os.path.exists(comment_file_path):
                    os.remove(comment_file_path)

        except Exception as e:
            result_message += f"\033[31mError editing metadata for RAR archive: {e}\033[0m\n"

        return result_message

    def show_metadata(self, archive_manager):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".rar"):
                result_message += "\033[31mInvalid archive type. Expected RAR archive.\033[0m\n"
                return result_message

            comment_file_path = archive_manager.archive_path + ".txt"
            if os.path.exists(comment_file_path):
                with open(comment_file_path, "r") as comment_file:
                    comment = comment_file.read()
                    result_message += f"RAR Archive Comment:\n{comment}\n"
            else:
                result_message += "No comment file found for this RAR archive.\n"

        except Exception as e:
            result_message += f"\033[31mError showing metadata for {archive_manager.archive_path}: {e}\033[0m\n"

        return result_message

    def test(self, archive_manager):
        result_message = ""

        try:
            if not archive_manager.archive_path.endswith(".rar"):
                result_message += "\033[31mInvalid archive type. Expected RAR archive.\033[0m\n"
                return result_message

            unrar_path = r"C:\Program Files\WinRAR\unrar.exe"
            args = [unrar_path, 't', archive_manager.archive_path]
            result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                result_message += f"\033[32mRAR Archive {archive_manager.archive_path} is valid and has no errors.\033[0m\n"
            else:
                result_message += f"\033[31mRAR Archive {archive_manager.archive_path} may be corrupt or an error occurred.\033[0m\n"

        except Exception as e:
            result_message += f"\033[31mError testing {archive_manager.archive_path}: {e}\033[0m\n"

        return result_message


class AceStrategy(ArchiveStrategy):
    def create(self, archive_manager, file_names_or_dir):
        try:
            return "Creation of .ace archives is not supported."
        except Exception as e:
            return f"Error creating .ace archive: {e}"

    def extract(self, archive_manager, extract_path):
        try:
            return "Extraction of .ace archives is not supported."
        except Exception as e:
            return f"Error extracting .ace archive: {e}"

    def add(self, archive_manager, file_names_or_dir):
        try:
            return "Adding files to .ace archives is not supported."
        except Exception as e:
            return f"Error adding files to .ace archive: {e}"

    def remove(self, archive_manager, items_to_remove):
        try:
            return "Removing files from .ace archives is not supported."
        except Exception as e:
            return f"Error removing items from .ace archive: {e}"

    def edit_metadata(self, archive_manager, new_metadata):
        try:
            return "Editing metadata is not supported for ACE archives."
        except Exception as e:
            return f"Error editing metadata for ACE archive: {e}"

    def show_metadata(self, archive_manager):
        try:
            return "Showing metadata is not supported for ACE archives."
        except Exception as e:
            return f"Error showing metadata for ACE archive: {e}"

    def test(self, archive_manager):
        try:
            return "Testing .ace archives is not supported."
        except Exception as e:
            return f"Error testing ACE archive: {e}"