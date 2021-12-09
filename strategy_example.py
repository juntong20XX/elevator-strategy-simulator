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
    controller = None

    @staticmethod
    def get_nearest_elevator(target_floor: int, free_elevators: dict) -> int:
        """不检查电梯是否运行"""
        ls = [(i, abs(f - target_floor)) for i, (f, _, _, _) in free_elevators.items()]
        return min(ls, key=lambda x: x[1])[0]

    @staticmethod
    def get_up_floors(passenger: dict) -> list:
        """获取向上寻呼的楼层。传入值`passenger`应为`info["passenger"]`"""
        return [floor for floor, passengers in passenger.items()
                if passengers and any(p > floor for p in passengers)]

    @staticmethod
    def get_down_floors(passenger: dict) -> list:
        """获取向下寻呼的楼层。传入值`passenger`应为`info["passenger"]`"""
        return [floor for floor, passengers in passenger.items()
                if passengers and any(p < floor for p in passengers)]

    @staticmethod
    def get_free_elevators(elevator: list) -> dict:
        """获取空闲的电梯"""
        return {i: ls for i, ls in enumerate(elevator) if ls[1] is None}

    def open_door_and_up(self, elevator_num):
        """电梯开门并显示上行，之后分配该电梯前往方向，最后返回更新后的 up 值。
        使用方法
            open_and_up = self.open_door_and_up(elevator_num)
            info = yield next(open_and_up)
            info = yield next(open_and_up, info)
            assert info["say"] == "success"
            up = next(open_and_up)
        """
        print("电梯%d 开门，显示上行" % elevator_num)
        info = yield cmds.elevator_up(elevator_num)  # 电梯开门，显示上行
        assert info["say"] == "success"
        up = self.get_up_floors(info["passenger"])  # 更新向上寻呼楼层
        lo_inside = min(info["return"])  # 电梯内最低前往楼层
        # 电梯一定优先考虑“内需”，但考虑顺便载乘客
        max_people = info["elevator"][elevator_num][3]
        assert len(info["return"]) <= max_people  # XXX: 此代码用于测试是否存在“超载”，可删去
        if len(info["return"]) < max_people:  # 电梯未满载
            floor = info["elevator"][elevator_num][0]
            lo_up = [i for i in up if floor < i < lo_inside]
            if lo_up:
                goto = min(lo_up)
            else:
                goto = lo_inside
        else:  # 电梯已满载，前往电梯内最低目标楼层
            goto = lo_inside
        yield cmds.elevator_to(elevator_num, goto)
        yield up

    def open_door_and_down(self, elevator_num):
        """电梯开门并显示下行，之后分配该电梯前往方向，最后返回更新后的 down 值。
        使用方法
            open_and_down = self.open_door_and_down(elevator_num)
            info = yield next(open_and_down)
            info = yield next(open_and_down, info)
            assert info["say"] == "success"
            down = next(open_and_down)
        """
        print("电梯%d 开门，显示下行" % elevator_num)
        info = yield cmds.elevator_down(elevator_num)  # 电梯开门，显示下行
        assert info["say"] == "success"
        down = self.get_down_floors(info["passenger"])  # 更新向下寻呼楼层
        hi_inside = max(info["return"])  # 电梯内最高前往楼层
        # 电梯一定优先考虑“内需”，但考虑顺便载乘客
        max_people = info["elevator"][elevator_num][3]
        assert len(info["return"]) <= max_people  # XXX: 此代码用于测试是否存在“超载”，可删去
        if len(info["return"]) < max_people:  # 电梯未满载
            floor = info["elevator"][elevator_num][0]
            hi_down = [i for i in down if floor > i > hi_inside]  # 下降途中可以上电梯的乘客
            if hi_down:
                goto = max(hi_down)
            else:
                goto = hi_inside
        else:  # 电梯已满载，下行前往电梯内最高目标楼层
            goto = hi_inside
        yield cmds.elevator_to(elevator_num, goto)
        yield down

    def init_elevator(self, info: dict):
        """初始化电梯，也就是给没有任务的电梯分配任务。"""
        free_elevators = self.get_free_elevators(info["elevator"])

        if not free_elevators:
            # 如果没有空电梯，则停止分配
            return

        down = self.get_down_floors(info["passenger"])
        up = self.get_up_floors(info["passenger"])
        if not (up or down):
            # 如果没有请求，则终止
            return

        # 先考虑电梯停留层有需求
        for i, (f, _, _, m) in free_elevators.copy().items():
            if f in up:
                open_and_up = self.open_door_and_up(i)
                info = yield next(open_and_up)
                info = yield open_and_up.send(info)
                assert info["say"] == "success"
                up = next(open_and_up)
                free_elevators.pop(i)
            elif f in down:
                open_and_down = self.open_door_and_down(i)
                info = yield next(open_and_down)
                info = yield open_and_down.send(info)
                assert info["say"] == "success"
                down = next(open_and_down)
                free_elevators.pop(i)
        req = set(up + down)  # req是乘梯需求

        # 响应请求
        while req and free_elevators:  # 条件是有乘梯需求且有空电梯
            goto = max(req)  # 前往最高请求楼层
            elevator_num = self.get_nearest_elevator(goto, free_elevators)
            at = free_elevators.pop(elevator_num)[0]  # 这里从free_elevators中删去了已选中的电梯
            if at < goto:
                # 电梯上行，此时可能有路过的请求
                up_passed = [i for i in up if at < i < goto]
                if up_passed:
                    goto = min(up_passed)
            info = yield cmds.elevator_to(elevator_num, goto)
            assert info["say"] == "success"
            # 刷新数据
            up = self.get_up_floors(info["passenger"])
            if goto in up:
                up.remove(goto)
                goto = None
            down = self.get_down_floors(info["passenger"])
            if goto in down:
                down.remove(goto)
            req = set(up + down)

    def loop_call(self, info: dict) -> dict:
        """每次循环时被调用，注意执行速度。
        """
        if self.controller is None:
            print("这里是周期调用……")
        if self.controller is not None:
            try:
                cmd = self.controller.send(info)
            except StopIteration:
                self.controller = None
                return cmds.Bye
            else:
                return cmd

        if cmds.said_routine(info):
            # 轮询的初始操作
            self.controller = self.init_elevator(info)
            try:
                return next(self.controller)
            except StopIteration:
                self.controller = None
                return cmds.Bye
        else:
            # 应该不会有这种情况
            raise Exception("轮询调用函数在该周期非第一次调用时，没有控制器方法")

    def elevator_arrive_call(self, info: dict) -> dict:
        """当电梯到达时执行， info 有额外值`arrive elevator`，该值传入后不会更新
其类型为list,“到达的电梯”的序号、所在楼层、上次停靠楼层、每个乘客目标元组
         #example -> [(0, 1, 1, (2, 3, 4)), (1, 2, 1, (2, 5)), (4, 3, 4, ()), ...]
    在`loop_call`之前执行。
        """
        if self.controller is None:
            print("这里是循环调用……")
        if self.controller is not None:
            try:
                cmd = self.controller.send(info)
            except StopIteration:
                self.controller = None
                return cmds.Bye
            else:
                return cmd

        assert cmds.said_routine(info), "到达调用函数在该周期非第一次调用时，没有控制器方法"

        self.controller = self.arrive_iterator(info)
        try:
            return next(self.controller)
        except StopIteration:
            self.controller = None
            return cmds.Bye

    def arrive_iterator(self, info):
        for index, floor, last, inside in info["arrive elevator"]:
            print(index, floor, last, inside)
            if not inside:
                continue
            if last < floor:
                # 电梯正在上行
                assert min(inside) > floor, "电梯上行时，内部有需要向下的乘客"  # XXX: 测试时使用
                up = self.get_up_floors(info["passenger"])
                if floor in up:
                    # 恰好有乘客在经停层
                    open_and_up = self.open_door_and_up(index)
                    info = yield next(open_and_up)
                    info = yield open_and_up.send(info)
                    assert info["say"] == "success"
                else:
                    print("电梯", index, "不上客，继续上行")
                    # 不上客，继续上行  || 此代码复制自 `self.open_door_and_up`
                    lo_inside = min(inside)  # 电梯内最低前往楼层
                    # 电梯一定优先考虑“内需”，但考虑顺便载乘客
                    max_people = info["elevator"][index][3]
                    assert len(inside) <= max_people  # XXX: 此代码用于测试是否存在“超载”，可删去
                    if len(inside) < max_people:  # 电梯未满载
                        lo_up = [i for i in up if floor < i < lo_inside]
                        if lo_up:
                            goto = min(lo_up)
                        else:
                            goto = lo_inside
                    else:  # 电梯已满载，前往电梯内最低目标楼层
                        goto = lo_inside
                    info = yield cmds.elevator_to(index, goto)
                    assert info["say"] == "success"

            else:
                # 电梯正在下行
                assert max(inside) < floor, "电梯下行时，内部有需要向上的乘客"  # XXX: 测试时使用
                down = self.get_down_floors(info["passenger"])
                if floor in down:
                    open_and_down = self.open_door_and_down(index)
                    info = yield next(open_and_down)  # 开门
                    info = yield open_and_down.send(info)  # 前往楼层
                    assert info["say"] == "success"
                else:
                    print("电梯", index, "不上客，继续下行")
                    # 不上客，继续下行  || 此代码复制自 `self.open_door_and_down`
                    hi_inside = max(inside)  # 电梯内最高前往楼层
                    # 电梯一定优先考虑“内需”，但考虑顺便载乘客
                    max_people = info["elevator"][index][3]
                    assert len(inside) <= max_people  # XXX: 此代码用于测试是否存在“超载”，可删去
                    if len(inside) < max_people:  # 电梯未满载
                        hi_down = [i for i in down if hi_inside < i < floor]  # 下降途中可以上电梯的乘客
                        if hi_down:
                            goto = max(hi_down)
                        else:
                            goto = hi_inside
                    else:  # 电梯已满载，下行前往电梯内最高目标楼层
                        goto = hi_inside
                    yield cmds.elevator_to(index, goto)


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
