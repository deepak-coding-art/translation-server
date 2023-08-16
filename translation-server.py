# Import library's
import socket
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
import socket
import json
import threading
import traceback

HostPort = 4000
secret_key = "123456"
buffer_size = 10 * 1024  # 10 KB in bytes


class TranslationService:
    def __init__(self, modelSize) -> None:
        # Variables
        self.translator = self.init_model(modelSize)

    # Init translation model
    def init_model(self, model_type="small", source_language="russian",  target_language="english"):
        print("Loading model..")
        # Define model and tokenizer
        if model_type == "medium":
            # Define 1.3B model
            model = AutoModelForSeq2SeqLM.from_pretrained(
                "facebook/nllb-200-1.3B")
            tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-1.3B")
        elif model_type == "large":
            # Define 2.5B model
            model = AutoModelForSeq2SeqLM.from_pretrained(
                "facebook/nllb-200-3.3B")
            tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-3.3B")
        else:
            # Define 600mil model
            model = AutoModelForSeq2SeqLM.from_pretrained(
                "facebook/nllb-200-distilled-600M")
            tokenizer = AutoTokenizer.from_pretrained(
                "facebook/nllb-200-distilled-600M")

        # Language codes
        Hindi_code = "hin_Deva"
        English_code = "eng_Latn"
        Russian_code = "rus_Cyrl"

        if source_language == 'russian':
            active_source_language = Russian_code
        if target_language == 'english':
            active_target_language = English_code

        # Create translation pipeline
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        translator = pipeline('translation', model=model, tokenizer=tokenizer, src_lang=active_source_language,
                              tgt_lang=active_target_language, max_length=1000, device=device)

        print(f"🟢 {model_type} Model loaded!")
        # Test translation is working correctly
        print("Running test_run...")
        text = "Сервер перевода запущен"
        result = translator(text)
        test_run = result[0]["translation_text"]
        print(f"{text} => {test_run}")
        print("🟢 Test run completed!")

        # Return the model
        return translator

    # Main function that returns translated string
    def translate(self, text: str):
        result = self.translator(text)
        translated_text = result[0]["translation_text"]
        return translated_text


class HandleSocket:
    def __init__(self) -> None:
        try:
            self.PORT = HostPort
            self.translator = TranslationService("small")
            self.server_running = True
            self.server_socket = None  # Initialize server socket to None
            self.start_server()
        except Exception as e:
            print("🔴 Error in server: ", e)
            traceback.print_exc()

    # Function to get local machine ip_address
    def get_local_ip(self):
        try:
            host_name = socket.gethostname()
            local_ip = socket.gethostbyname(host_name)
            return local_ip
        except Exception as e:
            print(f"🔴 Error getting local IP address: {e}")
            return '127.0.0.1'  # Use localhost as a fallback

    # Function to listen for incoming connections
    def start_server(self):
        HOST = self.get_local_ip()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, self.PORT))
        self.server_socket.listen(5)
        print(f"🟢 Server is listening on {HOST}:{self.PORT}")

        while True:
            client_socket, _ = self.server_socket.accept()
            client_thread = threading.Thread(
                target=self.handle_client, args=(client_socket,))
            client_thread.start()

    # Function to handle the "config" method
    def handle_config(self, data):
        try:
            model = data["model"]
            if model not in ["small", "medium", "large"]:
                return {"status": 400, "error": "Invalid model"}
            self.translator = TranslationService(model)
            return {"status": 200}
        except KeyError:
            return {"status": 400, "error": "Invalid data format"}

    # Function to handle the "handle_translation" method
    def handle_translation(self, data):
        try:
            input_text = data["text"]
            # Process the input text (e.g., convert to uppercase)
            output_text = self.translator.translate(input_text)
            return {"status": 200, "translation": output_text}
        except KeyError:
            return {"status": 400, "error": "Invalid data format"}

    def handle_check_active_connections(self):
        try:
            socket_count = threading.active_count() - 1
            return {"status": 200, "active_connections": socket_count}
        except:
            return {"status": 500, "error": "Can not get data"}

    # def close_server(self):
    #     try:
    #         if self.server_socket:
    #             self.server_socket.close()
    #             self.server_socket = None  # Set the socket to None to indicate it's closed
    #         self.server_running = False
    #         # Wait for all threads to complete
    #         # for thread in threading.enumerate():
    #         #     if thread != threading.current_thread():
    #         #         thread.join()
    #     except Exception as e:
    #         print("🔴 Error while closing server:", e)

    def check_admin(self, data):
        try:
            auth_token = data["auth_token"]
            if auth_token == secret_key:
                return True
            else:
                return False
        except:
            return False

    # Function to handle client connections
    def handle_client(self, client_socket):
        while self.server_running:
            try:
                data = client_socket.recv(buffer_size)
                if not data:
                    break

                decoded_data = json.loads(data.decode("utf-8"))

                is_admin = self.check_admin(decoded_data)
                if not is_admin:
                    response_json = json.dumps(
                        {"status": 401, "error": "Unauthorized access"})
                    client_socket.send(response_json.encode("utf-8"))
                    break

                if "method" in decoded_data:
                    method = decoded_data["method"]
                    if method == "config":
                        response_data = self.handle_config(decoded_data)
                    elif method == "translation":
                        response_data = self.handle_translation(decoded_data)
                    elif method == "check_active_connections":
                        response_data = self.handle_check_active_connections()
                    # elif method == "close_server":
                    #     is_admin = self.check_admin(decoded_data)
                    #     if is_admin["is_admin"]:
                    #         response_data = {"status": 200}
                    #     else:
                    #         response_data = is_admin
                    #     break
                    else:
                        response_data = {"error": "Invalid method"}
                else:
                    response_data = {"error": "Method not specified"}

                response_json = json.dumps(response_data)
                client_socket.send(response_json.encode("utf-8"))
            except Exception as e:
                print("🔴 Error in handling client:", e)
                break

        client_socket.close()


socketHandler = HandleSocket()


if __name__ == "__main__":
    socketHandler = HandleSocket()
