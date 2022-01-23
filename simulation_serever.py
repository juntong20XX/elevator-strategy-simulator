# -*- coding: utf-8 -*-
"""
模拟器控制服务器。

启动服务器方式如下：
with Server(host="127.0.0.1", port=500) as server:
    server.serve_forever()

上下行使用 tcp流，序列化格式为 json

服务器返回数据模板为:
    {"success": bool,  # 命令执行成功为 True, 失败为 False
     "return": XXX,    # 类型不定,为返回值，或错误类型；若返回值不支持序列化，优先执行format，其次是str
     "print": str,     # 执行函数时输出的值，或报错信息
     }

客户端上传模板为:
    {"attr": str,    # (必选)服务器指令或模拟器属性。若attr非服务器指令，则查找模拟器是否有对应的属性，有则执行action对应的行为
     "action": str,  # (必选)attr的执行方式，有call,和get，call为执行该属性，get为直接返回。对服务器指令，必须为call。
     "args": list,   # (可选)根据attr灵活提供，默认为空。
     "kargs": dict,  # (可选)根据attr灵活提供，默认为空。
     }
服务器指令有：
- get print: 立刻读取输出
- close server:
    关闭服务器，默认返回字符"OK"
- start simulation: 
    启动模拟器迭代器，注意启动前打开策略文件和环境文件。
    可选布尔值`run_gc`，默认False。详见Server.start_simulation_generator
- flush simulation:
    刷新模拟器迭代器，接受可选参`add_time`，默认为None。详见Server.flush_simulation_generator
"""
import socketserver as stsv
import sys
import json
import array
import os
import gc

import simulation

class StreemLikeArray(array.array):
    """字符串列表(array.array('u'))，定义了write和read选项，用于重载stdout."""
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
        self.server.original_stdout.write("run setup\n")
        self.server.original_stdout.flush()
    def finish(self):
        self.server.original_stdout.write("run finish\n")
        self.server.original_stdout.flush()
        if self.close_server:
            self.server.original_stdout.write("run server.close()\n")
            self.server.original_stdout.flush()
            # self.server.shutdown()  # 如文档所说，这么做会造成死锁
            self.server.server_close()
            self.server.original_stdout.write("finish server.close()\n")
            self.server.original_stdout.flush()
    
    def handle(self):
        """"""
        self.data = self.read_message()
        self.result = self.run_data()
        self.request.sendall(make_a_handle_request(*self.result))
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
        if self.data["action"] not in {"call", "get"}:
            return "字典action值错误"
        if "args" in self.data and not isinstance(self.data["args"], list):
            return "字典args值类型错误，应为list"
        if "kargs" in self.data and not isinstance(self.data["kargs"], dict):
            return "字典kargs值类型错误，应为dict"
    def run_data(self):
        check_result = self.check_data_format()
        if check_result is not None:
            return False, check_result, ""
        attr = self.data["attr"]
        action = self.data["action"]
        args = self.data.get("args", [])
        kargs = self.data.get("kargs", {})
        
        server_result = self.run_server_commands(attr, action, args, kargs)
        if server_result is not None:
            return server_result
        
        simulation_result = self.run_simulation_command(attr, action, args, kargs)
        return simulation_result
    def run_server_commands(self, attr, action, args, kargs) -> None or str:
        if action != "call":
            return
        if attr == "get print":
            return True, self.server.new_stdout.read(), ""
        elif attr == "close server":
            self.close_server = True
            return True, "OK", ""
        elif attr == "start simulation":
            try:
                ret = self.server.start_simulation_generator(*args, **kargs)
                print_text = self.server.new_stdout.read()
            except Exception as err:
                code = False
                ret = type(err).__name__
                print_text = self.server.new_stdout.read() + os.linesep + str(err)
            else:
                code = True
            return code, ret, print_text
        elif attr == "flush simulation":
            try:
                ret = self.server.flush_simulation_generator(*args, **kargs)
                print_text = self.server.new_stdout.read()
            except Exception as err:
                code = False
                ret = type(err).__name__
                print_text = self.server.new_stdout.read() + os.linesep + str(err)
            else:
                code = True
            return code, ret, print_text
    def run_simulation_command(self, attr, action, args, kargs):
        try:
            if action == "get":
                ret = getattr(self.server.simu, attr)
                print_text = self.server.new_stdout.read()
                return True, ret, print_text
            elif action == "call":
                ret = getattr(self.server.simu, attr)(*args, **kargs)
                print_text = self.server.new_stdout.read()
                return True, ret, print_text
        except Exception as err:
            print_text = self.server.new_stdout.read()
            return False, type(err).__name__, print_text + os.linesep + str(err)

def make_a_handle_request(is_success, return_object, print_text):
    data = {"success": is_success,
            "return": return_object,
            "print": print_text}
    try:
        ret = json.dumps(data)
    except json.JSONDecodeError:
        data["return"] = f"{data['return']}"
        ret = json.dumps(data)
    return ret.encode("utf-8")

class Server(stsv.TCPServer):
    """服务器对象，为套接字服务器。监听网络端口，提供模拟器的基本功能。"""
    def __init__(self, host: str = '127.0.0.1', port: int = 500,
                 handler = TcpHandler):
        self.simu = simulation.Simulation()
        self.original_stdout = sys.stdout
        self.new_stdout = None
        self.simulation_generator = None
        super().__init__((host, port), handler)
    def __enter__(self):
        sys.stdout = self.new_stdout = StreemLikeArray()
        return super().__enter__()
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.new_stdout = None
        sys.stdout = self.original_stdout
        super().__exit__(exc_type, exc_val, exc_tb)
    def serve_forever(self):
        """进入监听循环，因需要重定向stdout，需要在上下文环境中使用。"""
        assert self.new_stdout is not None, Exception("请在上下文交互中使用")
        super().serve_forever()
    def start_simulation_generator(self, run_gc=False):
        """生成并初始化模拟器迭代器，别忘了在运行前打开策略和环境文件。
参数run_gc若为真，则手动gc一次。添加手动gc功能是考虑到电梯策略可能启用了多进程。"""
        self.simulation_generator = self.simu.get_env_running_generator()
        if run_gc:
            gc.collect()
        return next(self.simulation_generator)
    def flush_simulation_generator(self, add_time=None):
        """需要在初始化模拟器迭代器后执行。add_time为传入值。"""
        return self.simulation_generator.send(add_time)

if __name__ == "__main__":
    with Server() as server:
        server.serve_forever()
