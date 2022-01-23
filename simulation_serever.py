# -*- coding: utf-8 -*-
"""
模拟器控制服务器。
"""
import socketserver as stsv
import sys
import json
import os
import array

import simulation

class StreemLikeArray(array.array):
    def __new__(cls):
        return super().__new__(cls, 'u')
    def write(self, text):
        self.extend(text)
    def read(self):
        ret = self.tounicode()
        while self:
            self.pop()
        return ret

class TcpHandler(stsv.BaseRequestHandler):
    def setup(self):
        self.close_server = False
    def finish(self):
        if self.close_server:
            self.server.shutdown()  # XXX:我不知道这有没有bug
    
    def handle(self):
        """"""
        self.data = self.read_message()
        self.result = self.run_data()
        
    def read_message(self) -> dict:
        """默认信息为json格式，可重写"""
        r = b""
        while 1:
            r += self.request.recv(1024)
            try:
                return json.loads(r.decode())
            except json.JSONDecodeError:
                pass
    def check_data_format(self):
        base_data_keys = {"attr", "action"}
        if not isinstance(self.data, dict):
            return "数据类型错误，应为字典"
        if set(self.data.keys()) & base_data_keys != base_data_keys:
            return "字典键错误"
    def run_data(self):
        check_result = self.check_data_format()
        if check_result is not None:
            return False, check_result
        attr = self.data["attr name"]
        action = self.data["action"]
        
        server_commands_result = self.run_server_commands(attr, action)
        if server_commands_result:
            return True, server_commands_result
        
        getattr(self.server.simu, attr)  # TODO
    def run_server_commands(self, attr, action) -> None or str:
        if action != "call":
            return
        if attr == "get print":
            return self.server.new_stdout.read()
        elif attr == "close server":
            self.close_server = True
            return "OK"

def make_a_handle_request(is_success, return_object):
    return {"success": is_success,
            "return": return_object}

class Server:
    def __init__(self, addr: str = '127.0.0.1', port: int = 500,
                 handler = TcpHandler):
        self.simu = simulation.Simulation()
        self.tcp_server = stsv.TCPServer((addr, port), handler)
        self.original_stdout = sys.stdout
        self.new_stdout = None
    def __enter__(self):
        sys.stdout = self.new_stdout = StreemLikeArray()
        return self
    def __exit__(self, *args):
        self.new_stdout = None
        sys.stdout = self.original_stdout
        self.tcp_server.server_close()
    def serve_forever(self):
        assert self.new_stdout, Exception("请在上下文交互中使用")
        self.tcp_server.serve_forever()

if __name__ == "__main__":
    server = Server()
    with server as s:
        s.serve_forever()
