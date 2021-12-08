#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""


class Strategy:
    """
输入 `info` 格式: dict
    {"say" : str, #表示为什么被调用，详见下文
     
     "passenger" : dict, #所有楼层的信息， key: 楼层数  value: 各个乘客的目标
     #example -> {1: (2, 3, ...), 2: (1, 3, ...), ...}
     
     "elevator" : list, #各个电梯的当前楼层，目标楼层，移动方向，最大载客数。索引对应电梯索引
     #example -> [(1, None, 0, 10), (2, 1, -1, 10), (3, 4, 1, 10), ...]
     }
- - -
输出 格式: dict
    {"cmd" : str, #执行的指令，详见下文。
     
     ... : ...
     }
- - -
output information `cmd` 输出的指令
1. "bye"  -> 结束执行，继续循环
2. "elevator to"  -> 指示电梯 N（从0开始数） 至 楼层 F 。需要指定整数值`N`和`F`
                     该指令返回上客后电梯内的乘客期望前往楼层，类型为 tuple
        example: {"cmd":"elevator to", "N":0, "F":None}
                 {"cmd":"elevator to", "N":-1, "F":10}
3. "elevator up" -> 指示电梯 N 向上。需要指定整数值`N`
                    该指令返回上客后电梯内的乘客期望前往楼层，类型为 tuple
4. "elevator down" -> 指示电梯 N 向下。需要指定整数值`N`
                    该指令返回上客后电梯内的乘客期望前往楼层，类型为 tuple
5. "label config update" -> 更新电梯 N 的显示标签。需指定整数值`N`和字典`data`
                    该指令返回 None。`data`会直接传给 tk.Label.config 
- - -
input information `say`
info["say"] -> "routine" #每次循环默认输入，不会传入额外值
        example : {"say": "routine",
                   "passenger": ..., "elevator": ...}
        
info["say"] -> "error" #表示执行出现错误， 有额外值`error`和`last command`
        example : {"say": "error",
                   "error": "...",     #str, 描述了错误原因。常见错误描述见下文
                   "last command": {}, #dict, 上一次输出的指令
                   "passenger": ..., "elevator": ...}
info["say"] -> "success" #表示执行成功， 有额外值`last command`和`return`
        example : {"say": "success",
                   "return": ..., #类型不确定，表示上一个指令的返回
                   "last command": {}, #dict, 上一次输出的指令
                   "passenger": ..., "elevator": ...}
- - -
input information `error`  常见错误描述
info["error"] -> "unknown command"
    """

    def loop_call(self, info: dict) -> dict:
        """每次循环时被调用，注意执行速度。
        """
        # TODO : your code

    def elevator_arrive_call(self, info: dict) -> dict:
        """当电梯到达时执行， info 有额外值`arrive elevator`，该值不会更新
其类型为list,“到达的电梯”的序号、所在楼层、上次停靠楼层、每个乘客目标元组
         #example -> [(0, 1, 1, (2, 3, 4)), (1, 2, 1, (2, 5)), (4, 3, 4, ()), ...]
    在`loop_call`之前执行。
        """
        # TODO : your code


class FastCmds:
    Bye = {"cmd": "bye"}

    @classmethod
    def elevator_to(cls, n: int, f: int):
        """指示电梯 N（从0开始数） 至 楼层 F（从1开始数） 。"""
        return {"cmd": "elevator to", "N": n, "F": f}

    @classmethod
    def said_routine(cls, info):
        return info["say"] == "routine"

    @classmethod
    def elevator_up(cls, n: int):
        """指示电梯 N 向上。"""
        return {"cmd": "elevator up", "N": n}

    @classmethod
    def elevator_down(cls, n: int):
        """指示电梯 N 向下。"""
        return {"cmd": "elevator down", "N": n}

    @classmethod
    def success_updown(cls, info):
        """命令执行成功 且 上一个命令为`elevator_up`或`elevator_down`。"""
        return (info["say"] == "success") and (
                info["last command"]["cmd"] in ("elevator up", "elevator down"))

    @classmethod
    def last_down(cls, info):
        """上一个命令为`elevator_down`。"""
        return "last command" in info and \
               info["last command"]["cmd"] == "elevator down"

    @classmethod
    def last_up(cls, info):
        """上一个命令为`elevator_up`。"""
        return "last command" in info and \
               info["last command"]["cmd"] == "elevator up"


cmds = FastCmds()

strategy = Strategy()
