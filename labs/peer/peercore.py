import socket
import threading
from cur.config import server_ports
from cur.core.adapters import TarGzAdapter, ZipAdapter, RarAdapter, AceAdapter
from cur.core.facade import ArchiveFacade
from cur.core.strategy import TarGzStrategy, ZipStrategy, RarStrategy, AceStrategy


def handle_peer(client_socket):
    client_socket.sendall(b'\033[33mWelcome!\nEnter command (help, create, extract, add, remove, edit_metadata, show_metadata, test, split exit) \033[0m')

    adapters = {
        'tar.gz': TarGzAdapter(TarGzStrategy()),
        'zip': ZipAdapter(ZipStrategy()),
        'rar': RarAdapter(RarStrategy()),
        'ace': AceAdapter(AceStrategy())
    }

    while True:
        command = client_socket.recv(1024).decode('utf-8').strip()
        if command not in ['create','extract','add','remove','edit_metadata','show_metadata','test','split','exit','help']:
            message = b"\033[31mUnknown command.\033[0m"
            client_socket.sendall(message)
        elif command == 'help':
            help_message = display_help()
            client_socket.sendall(help_message.encode('utf-8'))
            continue
        else:

            client_socket.sendall(b'\033[33mEnter archive type (tar.gz, zip, rar, ace):\033[0m')
            archive_type = client_socket.recv(1024).decode('utf-8').strip()
            client_socket.sendall(b'\033[33mEnter the full path to the archive: \033[0m')
            archive_path = client_socket.recv(1024).decode('utf-8').strip()
            if archive_type not in adapters:
                client_socket.sendall(b"\033[31mUnknown archive type.\033[0m")
                continue

            archive_facade = ArchiveFacade(archive_type, archive_path)

            if command == 'create':
                client_socket.sendall(b'\033[33mEnter files or directory to archive, separated by space:\033[0m')
                file_names_or_dir = client_socket.recv(1024).decode('utf-8').strip().split()
                response = archive_facade.create_archive(file_names_or_dir)
                response = add_command_prompt(response)
                client_socket.sendall(response.encode('utf-8'))
            elif command == 'extract':
                client_socket.sendall(b"\033[33mEnter the path where to extract:\033[0m")
                extract_path = client_socket.recv(1024).decode('utf-8').strip()
                response = archive_facade.extract_archive(extract_path)
                response = add_command_prompt(response)
                client_socket.sendall(response.encode('utf-8'))

            elif command == 'split':
                client_socket.sendall(b'\033[33mEnter the size of each part in megabytes:\033[0m')
                part_size_mb = int(client_socket.recv(1024).decode('utf-8').strip())
                part_size_bytes = part_size_mb * 1024 * 1024
                response = archive_facade.split_archive(part_size_bytes)
                response = add_command_prompt(response)
                client_socket.sendall(response.encode('utf-8'))

            elif command == 'add':
                client_socket.sendall(b'\033[33mEnter files or directory to add to the archive, separated by space:\033[0m')
                file_names_or_dir = client_socket.recv(1024).decode('utf-8').strip().split()
                response = archive_facade.add_files(file_names_or_dir)
                response = add_command_prompt(response)
                client_socket.sendall(response.encode('utf-8'))
            elif command == 'remove':
                client_socket.sendall(b'\033[33mEnter files to remove from the archive, separated by space:\033[0m')
                items_to_remove = client_socket.recv(1024).decode('utf-8').strip().split()
                response = archive_facade.remove_items(items_to_remove)
                response = add_command_prompt(response)
                client_socket.sendall(response.encode('utf-8'))
            elif command == 'edit_metadata':
                client_socket.sendall(b'\033[33mEnter new metadata for the archive:\033[0m')
                new_metadata = client_socket.recv(1024).decode('utf-8').strip()
                response = archive_facade.edit_metadata(new_metadata)
                response = add_command_prompt(response)
                client_socket.sendall(response.encode('utf-8'))
            elif command == 'show_metadata':
                response = archive_facade.show_metadata()
                response = add_command_prompt(response)
                client_socket.sendall(response.encode('utf-8'))
            elif command == 'test':
                response = archive_facade.test_archive()
                response = add_command_prompt(response)
                client_socket.sendall(response.encode('utf-8'))

            else:
                client_socket.sendall(b"\033[31mUnknown command.\033[0m")

def add_command_prompt(response):
    return response + '\033[33m\nEnter command (create, extract, add, remove, edit_metadata, show_metadata, test, split exit):\033[0m '

def find_free_port():
    for port in server_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return None

def handle_client_peer_wrapper(client_socket):
    try:
        handle_peer(client_socket)
    except (ConnectionAbortedError, ConnectionResetError) as exp:
        pass
    finally:
        client_socket.close()


def display_help():
    help_text = """
    \033[33mAvailable commands:
    create - Create a new archive
    extract - Extract files from an archive
    add - Add files to an archive
    remove - Remove files from an archive
    edit_metadata - Edit archive metadata
    show_metadata - Display archive metadata
    test - Test archive integrity
    split - Split an archive into parts
    exit - Exit the program
    help - Display this help message\033[0m
    """
    return help_text

def start_server():
    free_port = find_free_port()
    if free_port is None:
        return
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', free_port))
    server_socket.listen(1)

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client_peer_wrapper, args=(client_socket,))
        client_thread.start()

def start_client():
    port = find_free_port()
    if port is None:
        return
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', port))

    try:
        data = client_socket.recv(1024).decode('utf-8')
        print(data)
        while True:
            command = input('[-]')
            client_socket.sendall(command.encode('utf-8'))
            data = client_socket.recv(4096).decode('utf-8')
            print(data)
    finally:
        client_socket.close()

def main():
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    client_thread = threading.Thread(target=start_client)
    client_thread.start()
    server_thread.join()
    client_thread.join()


if __name__ == '__main__':
    main()
