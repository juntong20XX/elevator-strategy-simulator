# 电梯算法模拟器

## 简介

这是一个2021未来城市计划黑客马拉松参赛项目，用于创建图形界面模拟环境来测试电梯执行策略。该模拟器可以实时显示电梯的状态，动态增减呼梯乘客，并支持动态增加楼层、电梯数量等。

## 使用方法

运行` simulation.py`打开图形界面。或者实例化`simulation.Simulation`，并执行`.mainloop`方法。

非图形界面下：

| 方法名                    | 功能                                                         | 参数           | 作用                   |
| ------------------------- | ------------------------------------------------------------ | -------------- | ---------------------- |
| open_environment_file     | 加载环境文件                                                 | `path`         | 文件路径，类型为`str`  |
| open_strategy_file        | 加载策略文件                                                 | `path`         | 文件路径，类型为`str`  |
| get_env_running_generator | 返回一个迭代器。执行迭代器会刷新一次模拟环境，并返回当前模拟环境的周期。 |                |                        |
| get_elevator_label_config | 获取电梯对象显示标签的属性                                   | option         | 指定获取的属性         |
|                           |                                                              | elevator_index | 获取指定电梯或所有电梯 |

环境文件和策略文件的用法详见模板的注释。有环境示例`env_example.py`和策略示例`strategy_example.py`。该策略示例支持动态增减楼层和电梯数。

`simulation_server.py`为服务器文件，通过`simulation_server.Server`启动套接字服务器。服务器上传、下传数据均以json格式序列化。

服务器返回数据模板为:

```python
 {"success": bool,  # 命令执行成功为 True, 失败为 False
  "return": XXX,    # 类型不定,为返回值，或错误类型；若返回值不支持序列化，优先执行format，其次是str
  "print": str,     # 执行函数时输出的值，或报错信息
}
```

客户端上传模板为:

   ```python
   {"attr": str,    # (必选)服务器指令或模拟器属性。若attr非服务器指令，则查找模拟器是否有对应的属性，有则执行action对应的行为
    "action": str,  # (必选)attr的执行方式，有call,和get，call为执行该属性，get为直接返回。对服务器指令，必须为call。
    "args": list,   # (可选)根据attr灵活提供，默认为空。
    "kargs": dict,  # (可选)根据attr灵活提供，默认为空。
   }
   ```

服务器指令有：
- `get print`: 
    立刻读取输出

- `close server`:
    关闭服务器，默认返回字符"OK"
    
- `start simulation`: 
    启动模拟器迭代器，注意启动前打开策略文件和环境文件。
    可选布尔值`run_gc`，默认False。详见`Server.start_simulation_generator`
    
- `flush simulation`:
    刷新模拟器迭代器，接受可选参`add_time`，默认为None。详见`Server.flush_simulation_generator`

## Demo

```python
# server
host, port = "l27.0.0.1", 500
with simulation_server.Server(host, port) as server:
    server.serve_forever()

# client
import socket, json
class Client:  # 不知道是不是我测试环境的问题，每次发送和读取后都需要重新连接。
    def __init__(host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     	self.sock.connect((host, port))
    def read():
        r = b""
        while 1:
            r += self.sock.recv(1024)
            try:
                return json.loads(r.decode())
            except json.JSONDecodeError:
                pass
    def send_command(cmd, act, *arg, **karg):
        data = json.dumps({"attr": cmd, "action": act, "args": arg, "kargs": karg})
        return self.sock.send(data.encode())


# 客户端命令服务器运行模拟环境
client = Client(host, port)

client.send("open_environment_file", "call", "环境文件路径")
client.read()  # {'success': True, 'return': None, 'print': ''}
client.send("open_strategy_file", "call", "模拟文件路径")
client.read()  # {'success': True, 'return': None, 'print': ''}

client.send_command("start simulation", "call")
client.read()  # {'success': True, 'return': 1642933792.8631523, 'print': ''}
# 此时模拟环境已经启动，接下来可用"flush simulation"指令刷新环境
client.send_command("flush simulation", "call")
client.read()  # {'success': True, 'return': 1642933841.7025418, 'print': ''} 1642933841.7025418为模拟环境的时间值
```

## 更新说明

1. 将`get_env_running_iter`重命名为`get_env_running_generator`，
2. 添加了服务器系统。

## TODO

- 修改显示区域“电梯前往”错误的 bug。
- 添加版本系统。
- 优化服务器功能，如超时处理

## 历史更新记录

版本：（2022-1-22，晚上）

1. 更新和添加了非图形界面情况api，并更新了文档；
2. 在环境文件中添加了方法，可供开发者在加载环境后手动更新数据。

版本：（2021-12-10，下午）

1. 添加了重载电梯、乘客的方法，并在UI中添加了对应按键；
2. 优化了刷新楼层乘客信息刷新算法；
3. 在电梯信息界面添加了乘客数量显示面板；
4. 添加了布尔变量`runningUI`，用于记录是否在运行图像界面，从而优化与图形界面捆绑的方法；
5. 运行策略时自动锁定图形界面修改电梯数、楼层数、最大载客的按钮。

版本：（2021-12-9，早晨）

1. 修改了策略示例`max`函数传入值错误的bug

版本：(2021-12-8，夜间更新)

1. 修改了策略函数标准传入值 `info["elevator"]` 。该列表的元素增加了一个整数值表示该电梯的最大载客量。
2. 按照`PyCharm`的提示格式化了环境、策略模板。
3. 重写了策略示例，新的策略示例仍支持动态增减电梯数、电梯最大载客数；且代码更加优雅，策略分配更加合理。
