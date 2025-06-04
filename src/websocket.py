import hashlib
import base64

import main
import ws_frame


def isValid_WSRequest(method, target, http_version, headers_map):
    # We are trying to see if the WS handshake is valid
    is_get = method == "GET"
    # HTTP_version >= 1.1
    http_version_no = float(http_version.split("/")[1])
    http_version_isValid = http_version_no >= 1
    # Checking if the headers are complete
    valid_headers = (
        ("upgrade" in headers_map and headers_map.get("upgrade") == "websocket")
        and ("connection" in headers_map and headers_map.get("connection") == "Upgrade")
        and ("sec-websocket-key" in headers_map)
    )
    return is_get and http_version_isValid and valid_headers


MAGIC_WEBSOCKET_UUID_STRING = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def generate_sec_websocket_accept(sec_websocket_key):
    # We generate the accept key by concatenating the sec-websocket-key
    # and the magic string, Sha1 hashing it, and base64 encoding it.
    combined = sec_websocket_key + MAGIC_WEBSOCKET_UUID_STRING
    hashed_combined_string = hashlib.sha1(combined.encode())
    encoded = base64.b64encode(hashed_combined_string.digest())
    return encoded


WS_ENDPOINT = "/websocket"


def handle_WS_handshake_request(client_socket, ws_sockets, headers_map):
    # Save this socket in the WS sockets list so we will know to speak WS with
    # it in the future.
    ws_sockets.append(client_socket)
    # Generation of an accept key which from the sec-websocket-key and magic string
    sec_websocket_accept_value = generate_sec_websocket_accept(
        headers_map.get("sec-websocket-key")
    )

    # We can now build the response, telling the client we're switching
    # protocols while providing the key.
    websocket_response = ""
    websocket_response += "HTTP/1.1 101 Switching Protocols\r\n"
    websocket_response += "Upgrade: websocket\r\n"
    websocket_response += "Connection: Upgrade\r\n"
    websocket_response += (
        "Sec-WebSocket-Accept: " + sec_websocket_accept_value.decode() + "\r\n"
    )
    websocket_response += "\r\n"
    print("\nresponse:\n", websocket_response)

    client_socket.send(websocket_response.encode())


def handle_websocket_message(client_socket, input_sockets, ws_sockets):
    # Let's assume that we get a full single frame in each recv (may not
    # be true IRL)
    data_in_bytes = client_socket.recv(main.buffer_size)

    websocket_frame = ws_frame.WebsocketFrame()
    websocket_frame.populateFromWebsocketFrameMessage(data_in_bytes)

    print("Received message:", websocket_frame.get_payload_data().decode("utf-8"))
    return
