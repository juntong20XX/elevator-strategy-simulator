#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import hashlib
import bisect

PLAN_TAKE = 1  # 预计每层登上电梯的人数
PLAN_OUT = 1  # 预计每层下电梯的人数
FLOOR = 5  # 楼层数
UP_TIME = 5  # 显示预计时间使用的移动楼层时间
OPEN_TIME = 30  # 显示预计时间使用的开门停留时间


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

    def __init__(self):
        self.going_to_dict = {"list": [], "points": [], "inside numbers": []}
        self.cache = ""  # hashlib.md5(format(d).encode()).hexdigest()
        self.controller = None
        self.predict_text = ""

    @staticmethod
    def get_up_floors(passenger: dict) -> list:
        """获取向上寻呼的楼层。传入值`passenger`应为`info["passenger"]`结果由小到大排列"""
        return sorted(floor for floor, passengers in passenger.items()
                      if passengers and any(p > floor for p in passengers))

    @staticmethod
    def get_down_floors(passenger: dict) -> list:
        """获取向下寻呼的楼层。传入值`passenger`应为`info["passenger"]`结果由小到大排列"""
        return sorted(floor for floor, passengers in passenger.items()
                      if passengers and any(p < floor for p in passengers))

    def update_going_to_dict(self, at, direction, max_passengers, inside, passengers):
        # print("running update_going_to_dict")
        # print(at, direction, max_passengers, inside)
        # print(passengers)
        ls = self.going_to_dict["list"]  # 电梯将响应的需求
        points = self.going_to_dict["points"]  # 电梯运行的拐点
        inside_number = self.going_to_dict["inside numbers"]  # 每个点预计人数
        ls.clear()
        points.clear()
        inside_number.clear()
        if not (inside or passengers):  # 电梯里没人，楼里没有呼梯
            return
        plan_inside_num = len(inside)
        plan_inside_passengers = set(inside)
        up = self.get_up_floors(passengers)  # 向上需求的楼层
        down = self.get_down_floors(passengers)  # 向下需求的楼层
        floor = at  # 这段代码是为了去除开发环境错误的警告

        if not direction:  # 若电梯没有运行方向，那必然没有goto
            if inside:  # 电梯内有乘客
                if inside[0] < at:
                    direction = -1
                else:
                    direction = 1
            elif at in up:  # 电梯内无乘客，所在楼层有向上需求
                direction = 1
            elif at in down:  # 电梯内无乘客，所在楼层有向下需求
                direction = -1
            elif any(floor > at for floor, p in passengers.items() if p):  # 电梯内无乘客，所在楼层无需求，电梯上方有需求
                direction = 1
            else:  # 电梯内无乘客，所在楼层无需求，电梯下方有需求
                direction = -1

        while up or down:
            if plan_inside_num < max_passengers:  # 未超载
                if plan_inside_passengers:  # 电梯内有乘客
                    close_func = min if direction == 1 else max
                    going_dire = up if direction == 1 else down
                    goto_side = FLOOR if direction == 1 else 1
                    closest = close_func(plan_inside_passengers)
                    for passing_floor in range(at + direction, closest, direction):
                        if passing_floor in going_dire:
                            # 将楼层添加至列表
                            ls.append((passing_floor, direction))
                            plan_inside_passengers.add(goto_side)  # 默认上客前往最极端的地点
                            plan_inside_num += PLAN_TAKE
                            inside_number.append(plan_inside_num)
                            if plan_inside_num > max_passengers:  # 超载了
                                break
                            elif plan_inside_num == max_passengers:  # 满载且运送了该楼层全部乘客
                                going_dire.remove(passing_floor)
                                break
                            going_dire.remove(passing_floor)  # 未满载且运送了该楼层全部乘客
                    # 将电梯内最近前往楼层添加至列表
                    ls.append((closest, None))
                    plan_inside_passengers.remove(closest)
                    plan_inside_num -= PLAN_OUT
                    inside_number.append(plan_inside_num)
                    at = closest
                else:  # 电梯没有乘客
                    if direction == 1:
                        hi_up = up[bisect.bisect_right(up, at):]
                        hi_down = down[bisect.bisect_right(down, at):]
                        if at in up:
                            ls.append((at, direction))
                            plan_inside_passengers.add(FLOOR)
                            plan_inside_num += PLAN_TAKE
                            inside_number.append(plan_inside_num)
                            if plan_inside_num <= max_passengers:
                                up.remove(at)
                        elif hi_up:
                            for floor in hi_up:
                                ls.append((floor, 1))
                                plan_inside_passengers.add(FLOOR)
                                plan_inside_num += PLAN_TAKE
                                inside_number.append(plan_inside_num)
                                if plan_inside_num > max_passengers:  # 超载了
                                    break
                                elif plan_inside_num == max_passengers:  # 满载且运送了该楼层全部乘客
                                    up.remove(floor)
                                    break
                                up.remove(floor)
                            at = floor  # 更新地址
                        elif hi_down:
                            points.append((-1, len(ls)))  # 添加拐点
                            for floor in reversed(hi_down):
                                ls.append((floor, -1))
                                plan_inside_passengers.add(1)
                                plan_inside_num += PLAN_TAKE
                                inside_number.append(plan_inside_num)
                                if plan_inside_num > max_passengers:  # 超载了
                                    break
                                elif plan_inside_num == max_passengers:  # 满载且运送了该楼层全部乘客
                                    down.remove(floor)
                                    break
                                down.remove(floor)
                            direction = -1  # 更新移动方向
                            at = floor  # 更新地址
                        else:  # 反向
                            points.append((-1, len(ls)))  # 添加拐点
                            direction = -1
                    else:  # 电梯向下
                        lo_up = up[:bisect.bisect_left(up, at)]
                        lo_down = down[:bisect.bisect_left(down, at)]
                        if at in down:
                            ls.append((at, direction))
                            plan_inside_passengers.add(1)
                            plan_inside_num += PLAN_TAKE
                            inside_number.append(plan_inside_num)
                            if plan_inside_num <= max_passengers:
                                down.remove(at)
                        elif lo_down:
                            for floor in reversed(lo_down):
                                ls.append((floor, -1))
                                plan_inside_passengers.add(1)
                                plan_inside_num += PLAN_TAKE
                                inside_number.append(plan_inside_num)
                                if plan_inside_num > max_passengers:  # 超载了
                                    break
                                elif plan_inside_num == max_passengers:  # 满载且运送了该楼层全部乘客
                                    down.remove(floor)
                                    break
                                down.remove(floor)
                            at = floor  # 更新地址
                        elif lo_up:
                            points.append((1, len(ls)))  # 添加拐点
                            for floor in lo_up:
                                ls.append((floor, 1))
                                plan_inside_passengers.add(FLOOR)
                                plan_inside_num += PLAN_TAKE
                                inside_number.append(plan_inside_num)
                                if plan_inside_num > max_passengers:  # 超载了
                                    break
                                elif plan_inside_num == max_passengers:  # 满载且运送了该楼层全部乘客
                                    up.remove(floor)
                                    break
                                up.remove(floor)
                            direction = -1  # 更新移动方向
                            at = floor  # 更新地址
                        else:  # 反向
                            points.append((1, len(ls)))  # 添加拐点
                            direction = 1
            else:  # 已满载
                # 只考虑电梯内的乘客
                if direction == 1:  # 电梯上行
                    to = min(plan_inside_passengers)
                else:
                    to = max(plan_inside_passengers)
                ls.append((to, None))
                plan_inside_passengers.remove(to)
                plan_inside_num -= PLAN_OUT
                inside_number.append(plan_inside_num)
                at = to

    def loop_call_iter(self, info):
        passengers = info["passenger"]
        cache = hashlib.md5(format(passengers).encode()).hexdigest()
        if self.cache != cache:
            self.cache = cache
            at, goto, direction, max_passengers = info["elevator"][0]
            inside = yield {"cmd": "passengers in elevator", "N": 0}
            inside = inside["return"]
            self.update_going_to_dict(at, direction, max_passengers, inside, passengers)

            if not direction:  # 电梯空闲
                goto_next = self.get_next_iter(at, goto, direction, max_passengers)
                value = None
                while 1:
                    value = yield goto_next.send(value)

    def get_next_iter(self, at, goto, direction, max_passengers):
        while self.going_to_dict["list"]:
            # print("running get_next_iter")
            f, d = self.going_to_dict["list"][0]
            if d is None:  # 电梯下客
                if f == goto:  # 说明什么都不用做
                    return
                elif f == at:  # 电梯已经在应下客楼层了
                    self.going_to_dict["list"].pop(0)
                else:  # 需要修改电梯目标楼层
                    yield cmds.elevator_to(0, f)
                    return
            else:  # 电梯移动
                if f == at:  # 电梯开门
                    info = yield cmds.elevator_up(0) if d == 1 else cmds.elevator_down(0)
                    passengers = info["passenger"]
                    inside = info["return"]
                    self.cache = hashlib.md5(format(passengers).encode()).hexdigest()
                    self.update_going_to_dict(at, direction, max_passengers, inside, passengers)
                else:  # 命令电梯前往指定楼层
                    yield cmds.elevator_to(0, f)
                    return

    def loop_call(self, info: dict) -> dict:
        """每次循环时被调用，注意执行速度。
        """
        # print("running loop_call")
        if info["say"] == "success" and info["last command"]["cmd"] == "label config update":
            return cmds.Bye
        if self.controller is not None:
            try:
                cmd = self.controller.send(info)
            except (StopIteration, RuntimeError):
                self.controller = None
                at, _, direction, max_passengers = info["elevator"][0]
                new_text = self.get_predict_text(at, direction, max_passengers)
                if self.predict_text == new_text:
                    return cmds.Bye
                else:
                    return {"cmd": "label config update", "data": {"text": new_text}, "N": 0}
                # TODO:刷新预测显示

            else:
                return cmd

        if cmds.said_routine(info):
            # 轮询的初始操作
            self.controller = self.loop_call_iter(info)
            try:
                return next(self.controller)
            except (StopIteration, RuntimeError):
                self.controller = None
                return cmds.Bye

    @staticmethod
    def text_dict_to_str(d):
        text_list = []
        for i in range(1, FLOOR + 1):
            text = "F" + str(i).ljust(3)
            up, down = d[i]
            text += "up " + str(up).center(4) + "    "
            text += "down " + str(down).center(4)
            text_list.append(text)
        return "\n".join(text_list)

    def get_predict_text(self, at, direction, max_passengers):
        d = {f: [None, None] for f in range(1, 6)}
        tim = 0
        if not direction:
            if self.going_to_dict["list"]:
                d[at][self.going_to_dict["list"][0][1] == 1] = 0
            else:
                for plan_f in range(2, FLOOR):
                    tim = abs(plan_f - at) * UP_TIME
                    d[plan_f] = [tim, tim]
                d[1][1] = abs(at - 1) * UP_TIME
                d[FLOOR][0] = abs(FLOOR - at) * UP_TIME
                return self.text_dict_to_str(d)
        else:
            d[at][direction == 1] = tim
        for (plan_f, _plan_d), num in zip(self.going_to_dict["list"], self.going_to_dict["inside numbers"]):
            if not _plan_d:
                plan_d = 1 if at < plan_f else -1
            else:
                plan_d = _plan_d
            if num < max_passengers:
                for at in range(at+plan_d, plan_f, plan_d):
                    tim += UP_TIME
                    d[at][plan_d == 1] = tim
            if (plan_f == 1 and plan_d == -1) or (plan_f == FLOOR and plan_d == 1):
                continue
            tim += UP_TIME
            d[plan_f][plan_d == 1] = tim
            if _plan_d:
                tim += OPEN_TIME
            at = plan_f
        # TODO: 填充空白

        return self.text_dict_to_str(d)

    def elevator_arrive_call(self, info: dict) -> dict:
        """当电梯到达时执行， info 有额外值`arrive elevator`，该值不会更新
其类型为list,“到达的电梯”的序号、所在楼层、上次停靠楼层、每个乘客目标元组
         #example -> [(0, 1, 1, (2, 3, 4)), (1, 2, 1, (2, 5)), (4, 3, 4, ()), ...]
    在`loop_call`之前执行。
        """
        # print("running elevator_arrive_call")
        if self.controller is not None:
            try:
                cmd = self.controller.send(info)
            except (StopIteration, RuntimeError):
                self.controller = None
                return cmds.Bye
            else:
                return cmd

        if cmds.said_routine(info):
            # 轮询的初始操作
            at, goto, direction, max_passengers = info["elevator"][0]
            self.controller = self.get_next_iter(at, goto, direction, max_passengers)
            try:
                return next(self.controller)
            except (StopIteration, RuntimeError):
                self.controller = None
                return cmds.Bye


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

# For testing
# passengers = {1: (),
#               2: (1, 5, 5, 5, 3, 4, 4, 3, 5, 3),
#               3: (4, 5, 1, 2, 1, 2, 5),
#               4: (3, 1, 3, 3, 3, 3, 3, 2),
#               5: (3, 3)}
# strategy.update_going_to_dict(1, 0, 10, (), passengers)
# print(strategy.get_predict_text(1, 0, 10))
