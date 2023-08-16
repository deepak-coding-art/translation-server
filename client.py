import socket
import json
buffer_size = 10 * 1024  # 10 KB in bytes


def send_request(socket, data):
    try:
        request_json = json.dumps(data)
        socket.send(request_json.encode("utf-8"))
        response = socket.recv(buffer_size).decode("utf-8")
        return json.loads(response)
    except Exception as e:
        print("Error:", e)
        return None


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("192.168.1.3", 10004))
auth_token = input("Enter Admin API key: ")

while True:
    print("--------------------- Select ---------------------")
    print("1. Send 'config' method")
    print("2. Send 'translation' method")
    print("3. Check active socket connections")
    # print("4. Close all server socket connections")
    print("5. Exit")
    choice = input("Select an option: ")
    print(f"------------ Choice {choice} ----------------")

    if choice == "1":
        model = input("Enter model value: ")
        request_data = {"auth_token": auth_token,
                        "method": "config", "model": model}
        response = send_request(client_socket, request_data)
    elif choice == "2":
        text = input("Enter input text: ")
        request_data = {"auth_token": auth_token,
                        "method": "translation", "text": text}
        response = send_request(client_socket, request_data)
    elif choice == "3":
        request_data = {"auth_token": auth_token,
                        "method": "check_active_connections"}
        response = send_request(client_socket, request_data)
    # elif choice == "4":
    #     token = input("Enter admin token: ")
    #     request_data = {"auth_token": auth_token, "method": "close_server", "token": token}
    #     response = send_request(client_socket, request_data)
    #     if (response["status"] == 200):
    #         client_socket.close()
    #         break
    elif choice == "5":
        client_socket.close()
        break
    else:
        print("Invalid choice")

    if response:
        print("Response:", response)

print("Client closed.")
