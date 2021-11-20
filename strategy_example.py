#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""


class Strategy:
    """
输入 `info` 格式: dict
    {"say" : str, #表示为什么被调用，详见下文
     
     "passenger" : dict, #所有楼层的信息， key: 楼层数  velue: 各个乘客的目标
     #example -> {1: (2, 3, ...), 2: (1, 3, ...), ...}
     
     "elevator" : list, #各个电梯的当前楼层，目标楼层，移动方向。索引对应电梯索引
     #example -> [(1, None, 0), (2, 1, -1), (3, 4, 1), ...]
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
5. "passengers in elevator" -> 获取电梯 N 内每个乘客期望前往楼层。需要指定整数值`N`
                    该指令返回类型为 tuple
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
info["error"] -> "unknow command"
    """

    def loop_call(self, info: dict) -> dict:
        '''每次循环时被调用，注意执行速度。
        '''
        to_go_floor = [floor for floor, v in info["passenger"].items() if v]
        free_elevators = [(idx, i[0]) for idx, i in enumerate(info["elevator"])
                          if i[1] is None]
        # 因为此函数在`elevator_arrive_call`后面执行，如果电梯内有乘客，
        # `elevator_arrive_call`会指派电梯。故此判断空闲方法合理。
        if not (to_go_floor and free_elevators):
            return {"cmd": "bye"}
        # 有想乘梯的乘客 且 有闲置的电梯
        floor = max(to_go_floor)
        elevator = min(free_elevators, key=lambda x: abs(x[1] - floor))[0]
        return {"cmd": "elevator to", "N": elevator, "F": floor}

    def elevator_arrive_call(self, info: dict) -> dict:
        '''当电梯到达时执行， info 有额外值`arrive elevator`，该值不会更新
其类型为list, “到达的电梯”的序号、所在楼层、上次停靠楼层、每个乘客目标元组
         #example -> [(1, 1, (2, 3, 4)), (2, 1, (2, 5)), (3, 4, ()), ...]
    在`loop_call`之前执行。
        '''
        if info["say"] == "routine":
            self.arrive_elevator = info["arrive elevator"]
            index, floor, _, inside = self.arrive_elevator.pop()
            if inside:
                # 优先考虑电梯内的乘客
                if max(inside) > floor:
                    return {"cmd": "elevator up", "N": index}
                else:
                    return {"cmd": "elevator down", "N": index}
            else:
                passengers = info["passenger"][floor]
                if not passengers:
                    if self.arrive_elevator:
                        info["cmd"] = "routine"
                        return self.elevator_arrive_call(info)
                    else:
                        return {"cmd": "bye"}
                if max(passengers) > floor:
                    return {"cmd": "elevator up", "N": index}
                else:
                    return {"cmd": "elevator down", "N": index}
        elif info["say"] == "success" and \
                info["last command"]["cmd"].endswith(("up", "down")):
            last = info["last command"]
            index = last["N"]
            is_up = last["cmd"].endswith("up")
            if is_up:
                floor = min(info["return"])
                return {"cmd": "elevator to", "N": index, "F": floor}
            else:
                floor = max(info["return"])
                return {"cmd": "elevator to", "N": index, "F": floor}
        elif info["say"] == "success" and \
                info["last command"]["cmd"] == "elevator to":
            if not self.arrive_elevator:
                return {"cmd": "bye"}
            index, floor, _, inside = self.arrive_elevator.pop()
            if inside:
                # 优先考虑电梯内的乘客
                if max(inside) > floor:
                    return {"cmd": "elevator up", "N": index}
                else:
                    return {"cmd": "elevator down", "N": index}
            else:
                passengers = info["passenger"][floor]
                if not passengers:
                    if self.arrive_elevator:
                        info["cmd"] = "routine"
                        return self.elevator_arrive_call(info)
                    else:
                        return {"cmd": "bye"}
                if max(passengers) > floor:
                    return {"cmd": "elevator up", "N": index}
                else:
                    return {"cmd": "elevator down", "N": index}
        else:
            raise Exception(info)


strategy = Strategy()
