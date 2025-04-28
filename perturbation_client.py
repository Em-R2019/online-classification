import socket
import time

class PerturbationClient:
    def __init__(self):
        self.SERVER_IP = "169.254.9.242"
        self.PORT = 5000
        self.socket = None
        self.connected = False

    def start(self):
        print("server ip: " + self.SERVER_IP)
        print("server port: " + str(self.PORT))

        # Create a persistent connection
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.SERVER_IP, self.PORT))
        print(f"Connected to server at {self.SERVER_IP}:{self.PORT}")
        self.connected = True

    def send(self):
        try:
            output = 1
            message = f"{output}"  # Format as a string

            # Send to MATLAB server
            self.socket.sendall(message.encode())
            print(f"Sent: {message.strip()}")

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        if self.connected:
            output = 0
            message = f"{output}"  # Format as a string with newline

            # Send to MATLAB server
            self.socket.sendall(message.encode())
            print(f"Sent: {message.strip()}")
            time.sleep(0.5)

            print("\nClosing connection...")
            self.socket.close()
            self.connected = False