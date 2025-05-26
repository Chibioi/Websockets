import socket
import select  # Provides access to the select() system call
# The select() system call monitor many file descriptors e.g sockets and wait to see if one or more of them are ready for some I/O operations


tcp_ip = "127.0.0.1"
tcp_port = 5010
buffer_size = 1024 * 1024

default_http_response = b"""<HTML><HEAD><meta http-equiv="content-type" content="text/html;charset=utf-8">\r\n
<TITLE>200 OK</TITLE></HEAD><BODY>\r\n
<H1>200 OK</H1>\r\n
Welcome to the default.\r\n
</BODY></HTML>\r\n\r\n"""


def main():
    tcp_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM
    )  # Address family is the AF.INET and the socket type is SOCK_STREAM
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((tcp_ip, tcp_port))
    tcp_socket.listen(1)
    print("Listening on port: ", tcp_port)
    input_sockets = [tcp_socket]  # Reading
    output_sockets = []  # Writing
    xlist = []  # For exceptional conditions e.g can indicate out-of-bounds data

    while True:
        # Get the sockets that are ready to be read (the first three of the tuple)
        readable_sockets = select.select(
            input_sockets, output_sockets, xlist, 5
        )[
            0
        ]  # Involving a system call (select()). Returns a list of sockets that are ready for Reading,
        # Writing and Exceptions. Because of the [0] it returns only the first index of the tuple which
        # is the sockets available for Reading which is assigned to the variable readable_sockets.
        for ready_socket in readable_sockets:
            # Make sure is not already closed
            if (
                ready_socket.fileno == -1
            ):  # returns the underlying file descriptor (e.g sockets in this case)
                # of the stream if it exists. An OSError is raised if the IO object does not use a file descriptor.
                continue
            if ready_socket == tcp_socket:
                print("Handling main door socket")
                HandleNewConnection(tcp_socket, input_sockets)
            else:
                print("Handling regular socket read")
                HandleRequest(ready_socket, input_sockets)


def HandleNewConnection(main_door_socket, input_sockets):
    # When we get a connection on the main socket, we want to accept the new
    # connection and add it to our input socket list. When we loop back around,
    # that socket will be ready to read from.
    client_socket, client_address = (
        main_door_socket.accept()
    )  # Returns two values which are conn(which is the new socket) and address(the address bounded to the s
    # ocket on the other end of the connection)
    print("New socket", client_socket.fileno(), "from address:", client_address)
    input_sockets.append(client_socket)


def HandleRequest(client_socket, input_sockets):
    print("Handling request from the client socket: ", client_socket.fileno())
    message = ""
    # Very naive approach: read until we find the last blank line
    while True:
        data_in_bytes = client_socket.recv(buffer_size)
        # Connection on client side has closed.
        if len(data_in_bytes) == 0:
            close_socket(client_socket, input_sockets)
            input_sockets.remove(client_socket)
            client_socket.close()
            return
        message_segment = data_in_bytes.decode()
        message += message_segment
        if len(message) > 4 and message_segment[-4:] == "\r\n\r\n":
            break
        print("Received message: ", message)
        (method, target, http_version, headers_map) = ParseRequest(message)

    print("method, target, http_version:", method, target, http_version)
    print("headers: ", headers_map)

    # For now, just return a 200. Should probably return length too, eh
    client_socket.send(b"HTTP/1.1 200 OK\r\n\r\n" + default_http_response)
    close_socket(client_socket, input_sockets)


# Pass the first line and headers from the request
def ParseRequest(request):
    headers_map = {}
    # Assume headers and body are split by '\r\n\r\n' and we always have them.
    # Also assume all headers end with'\r\n'.
    # Also assume it starts with the method.
    split_request = request.split("\r\n\r\n")[0].split("\r\n")
    [method, target, http_version] = split_request[0].split(" ")
    headers = split_request[1:]
    for header_entry in headers:
        [header, value] = header_entry.split(": ")
        # Headers are case insensitive, so we can just keep track in lowercase.
        headers_map[header.lower()] = value
    return (method, target, http_version, headers_map)


def close_socket():
    pass
