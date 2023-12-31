import hashlib
import os


class ChecksumManager:
    @staticmethod
    def calculate(files):
        checksums = {}
        for file in files:
            hasher = hashlib.md5()
            with open(file, 'rb') as f:
                buf = f.read()
                hasher.update(buf)
            checksums[file] = hasher.hexdigest()
        return checksums

    @staticmethod
    def save(checksums, filename):
        with open(filename, 'w') as f:
            for file, checksum in checksums.items():
                f.write(f"{file} {checksum}\n")

    @staticmethod
    def verify(archive_path, checksum_file):
        with open(checksum_file, 'r') as f:
            checksums = {line.split()[0]: line.split()[1] for line in f}

        for file, checksum in checksums.items():
            hasher = hashlib.md5()
            with open(os.path.join(archive_path, file), 'rb') as f:
                buf = f.read()
                hasher.update(buf)
            if hasher.hexdigest() != checksum:
                return False
        return True