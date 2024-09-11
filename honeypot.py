#!/usr/bin/env python2.7
import socket
import sys
import threading
import paramiko

# Generate keys with 'ssh-keygen -t rsa -f server.key'
HOST_KEY = paramiko.RSAKey(filename='server.key')
SSH_PORT = 2222
LOGFILE = 'logins.txt'  # File to log the user:password combinations to
LOGFILE_LOCK = threading.Lock()

class SSHServerHandler(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        with LOGFILE_LOCK:
            try:
                with open(LOGFILE, "a") as logfile_handle:
                    print(f"New login: {username}:{password}")
                    logfile_handle.write(f"{username}:{password}\n")
            except IOError as e:
                print(f"ERROR: Failed to write to logfile: {e}")
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

def handle_connection(client_socket):
    transport = paramiko.Transport(client_socket)
    transport.add_server_key(HOST_KEY)

    server_handler = SSHServerHandler()
    transport.start_server(server=server_handler)

    try:
        channel = transport.accept(10)  # Wait up to 10 seconds for a channel
        if channel:
            channel.close()
    except Exception as e:
        print(f"ERROR: Exception during connection handling: {e}")
    finally:
        transport.close()

def main():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('', SSH_PORT))
        server_socket.listen(100)

        paramiko.util.log_to_file('paramiko.log')

        print(f"Listening for connections on port {SSH_PORT}...")
        while True:
            try:
                client_socket, client_addr = server_socket.accept()
                print(f"Accepted connection from {client_addr}")
                threading.Thread(target=handle_connection, args=(client_socket,)).start()
            except Exception as e:
                print(f"ERROR: Failed to accept client connection: {e}")

    except Exception as e:
        print(f"ERROR: Failed to create or bind the server socket: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
