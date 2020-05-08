"""
Серверное приложение для соединений
"""
import datetime
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                tmp_login = decoded.replace("login:", "").replace("\r\n", "")
                if self.check_login(tmp_login):
                    self.login = tmp_login
                    self.transport.write(f"Привет, {self.login}!".encode())
                    if len(self.send_history()) > 1:
                        for message in self.send_history():
                            self.transport.write(f"\n{message}".encode())
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        
        now_time = datetime.datetime.now().strftime("%H:%M %d-%m-%Y")
        format_string = f"{now_time} {format_string}"
        
        if len(self.send_history()) < 11:
            self.server.history.append(format_string)
        else:
            self.server.history.pop(1)
            self.server.history.append(format_string)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")

    def send_history(self):
        return self.server.history

    def check_login(self, login):
        for tmp_clients in self.server.clients:
            if login == tmp_clients.login:
                self.transport.write(
                    f"Логин {login} занят, попробуйте другой".encode()
                )
                self.transport.close()
                return False
        return True


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = ["Последние сообщения чата:"]

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
