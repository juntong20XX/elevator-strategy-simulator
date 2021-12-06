#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 14 22:32:30 2021

@author: Juntong.Zhu21

注意：
保存环境时不仅会覆盖文件，乘客组也无法保存。
"""
import tkinter as tk, tkinter.messagebox, os, random, functools, time, sys
from copy import copy
from threading import Thread

from tktools import TextNumPanedWindow, NumButton, FileButton, Switch


class Simulation:
    ENV_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__),
                                     "env_template.py")
    STR_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__),
                                     "strategy_template.py")

    def __init__(self):
        # ----  init all gui windows  ----
        self._window = tk.Tk()
        try:
            from ctypes import windll
        except Exception:
            pass
        else:
            windll.shcore.SetProcessDpiAwareness(1)
            ScaleFactor = windll.shcore.GetScaleFactorForDevice(0)
            self._window.tk.call('tk', 'scaling', ScaleFactor / 75)
        self._window.protocol("WM_DELETE_WINDOW", self._closing)
        mainwindow = tk.PanedWindow(self._window,
                                    orient="horizontal",
                                    sashrelief="solid")
        ctrlwindow = tk.PanedWindow(mainwindow,
                                    orient="vertical",
                                    sashrelief="solid")
        self._envctrl_frame = tk.Frame(ctrlwindow)
        self._strategy_frame = tk.Frame(ctrlwindow)
        self._happend_frame = tk.Frame(mainwindow)

        mainwindow.pack(fill="both", expand=1)
        ctrlwindow.pack(fill="both", expand=1)

        mainwindow.add(ctrlwindow)
        mainwindow.add(self._happend_frame)
        ctrlwindow.add(self._envctrl_frame, minsize=10)
        ctrlwindow.add(self._strategy_frame, minsize=10)

        self._init_envctrl_frame()
        self._init_strategy_frame()
        self._init_happend_frame()

        # ---- init variates ----
        # `reflash_time`,`elevator_num`,`floor_level_num`
        # `environment_filepath` and `strategy_filepath`
        # all setted before
        self.passengers_groups = {}  # 当载入文件时被填充，表示所有乘客组
        self.floor_passengers = {}  # 当载入文件时被填充，记录每层应用的乘客组
        self.elevators = []  # 当载入文件时被填充，记录每个电梯对象
        self.isRunning = False  # 后台工作进程是否在运行
        self.worker = Worker(self)  # 后台工作进程函数所在对象
        self.Strategy = None  # 当载入文件时加载，策略方法

    def mainloop(self):
        self._window.mainloop()

    def __getattr__(self, name):
        if not name.startswith("_"):
            return getattr(self, f"_{name}")

    def _init_envctrl_frame(self):
        tk.Label(self._envctrl_frame,
                 text="环境显示器", relief="groove").pack(fill="x")
        file_ctrl = tk.PanedWindow(self._envctrl_frame,
                                   orient="horizontal",
                                   sashrelief="raised")
        self._env_file_btn = FileButton(file_ctrl, text="<点击打开环境项目>",
                                        change_text_with_path=True,
                                        command=self._env_file_cmd)
        self._env_run_btn = Switch(file_ctrl, text="点击执行", bg="green",
                                   text_b="点击停止", bg_b="red",
                                   command=self._env_run_cmd)
        file_ctrl.add(self._env_file_btn,
                      minsize=self._env_file_btn.winfo_reqwidth() // 3)
        file_ctrl.add(self._env_run_btn,
                      minsize=self._env_run_btn.winfo_reqwidth() // 3)
        main_frame = tk.PanedWindow(self._envctrl_frame, sashrelief="raised")
        host_ctrl = tk.Frame(main_frame)
        self._reflash_ctrl = TextNumPanedWindow(host_ctrl, "刷新速度", 0.1,
                                                (0.01, 11))
        self._save_env = FileButton(host_ctrl, text="创建环境文件", issave=1,
                                    command=self._save_env_cmd)
        self._save_str = FileButton(host_ctrl, text="创建策略文件", issave=1,
                                    command=self._save_str_cmd)
        self._reflash_ctrl.grid(column=0, row=0, pady=2, columnspan=2,
                                sticky="we")
        self._save_env.grid(column=0, row=1, pady=2, padx=1, sticky="we")
        self._save_str.grid(column=1, row=1, pady=2, padx=1, sticky="we")
        devices_ctrl = tk.Frame(main_frame)
        self._ele_num_ctrl = TextNumPanedWindow(devices_ctrl, "电梯数", 1,
                                                (1, 31), True)
        self._ele_num_ctrl.right_num["command"] = self._ele_num_ctrl_cmd
        self._flo_num_ctrl = TextNumPanedWindow(devices_ctrl, "楼层数", 10,
                                                (1, 1000), True)
        self._flo_num_ctrl.right_num["command"] = self._flo_num_ctrl_cmd
        self._ele_num_ctrl.grid(column=0, row=0, pady=2, sticky="we")
        self._flo_num_ctrl.grid(column=0, row=1, pady=2, sticky="we")
        elevator_info = tk.Frame(main_frame)
        tk.Label(elevator_info, text="电梯运行速度").grid(
            column=0, row=0, columnspan=2, sticky="we")
        self._ele_speed_ctrl = NumButton(elevator_info, False, (0, 60), 1,
                                         command=self._ele_speed_ctrl_cmd)
        self._ele_speed_ctrl.grid(column=0, row=1)
        tk.Label(elevator_info, text="秒/层").grid(column=1, row=1, sticky="we")
        self._ele_max_people = TextNumPanedWindow(elevator_info, "最大载客",
                                                  10, (2, 20), True)
        self._ele_max_people.grid(column=0, row=2, columnspan=2, sticky="we")

        file_ctrl.pack(fill="x")
        main_frame.pack(fill="both", expand=1)
        main_frame.add(host_ctrl)
        main_frame.add(devices_ctrl)
        main_frame.add(elevator_info)

    def _init_strategy_frame(self):
        tk.Label(self._strategy_frame, text="策略显示器",
                 relief="groove").pack(fill="x")
        main_frame = tk.PanedWindow(self._strategy_frame, sashrelief="raised",
                                    orient="vertical")
        ctrl_frame = tk.Frame(main_frame)
        show_frame = tk.Frame(main_frame)
        scroll = tk.Scrollbar(show_frame)
        self._env_info_list = tk.Listbox(show_frame,
                                         yscrollcommand=scroll.set,
                                         font=("Courier", 16))
        scroll["command"] = self._env_info_list.yview
        self._env_info_list.pack(fill="both", expand=1, side="left")
        scroll.pack(fill="y", side="right")

        self._strategy_file_btn = FileButton(ctrl_frame,
                                             text="<点击打开策略项目>",
                                             change_text_with_path=True,
                                             command=self._strategy_file_cmd)

        self._strategy_file_btn.pack(fill="x")
        main_frame.pack(fill="both", expand=1)
        main_frame.add(ctrl_frame)
        main_frame.add(show_frame)

    def _init_happend_frame(self):
        tk.Label(self._happend_frame, text="电梯状态显示器",
                 relief="groove").pack(fill="x", side="top")
        self._elevator_list = tk.PanedWindow(self._happend_frame,
                                             orient="horizontal",
                                             sashrelief="raised")
        self._elevator_list.pack(fill="both", side="bottom", expand=1)

    @property
    def reflash_time(self):
        '刷新速度，可以将其当作常量获取和修改，支持动态修改。'
        return self._reflash_ctrl.number

    @reflash_time.setter
    def reflash_time(self, value):
        if num := self._reflash_ctrl.change_num(value):
            raise ValueError(num)

    @property
    def elevator_num(self):
        '电梯数量，可以将其当作常量获取和赋值修改。'
        return self._ele_num_ctrl.number

    @elevator_num.setter
    def elevator_num(self, value):
        if self._ele_num_ctrl.change_num(value):
            raise ValueError
        if value > len(self.elevators):
            ln = len(self.elevators)
            for num in range(value - ln):
                ele = Elevator(self._elevator_list, num + ln + 1)
                self.elevators.append(ele)
                self._elevator_list.add(ele.frame)
        elif value < len(self.elevators):
            for _ in range(len(self.elevators) - value):
                obj = self.elevators.pop()
                self._elevator_list.remove(obj.frame)
        # 修改每个电梯UI的空间
        self._elevator_list.update()
        fill = self._elevator_list.winfo_width()
        sub = (fill - 1) // value
        for i in range(value - 2, -1, -1):
            fill -= sub
            self._elevator_list.sash_place(i, fill, 1)

    @property
    def elevator_max_people(self):
        "电梯最大载客"
        return self._ele_max_people.number

    @elevator_max_people.setter
    def elevator_max_people(self, value):
        self._ele_max_people.change_num(value)

    @property
    def floor_level_num(self):
        "楼层数，可以将其当作常量获取和赋值修改，应通过加载环境文件修改。"
        return self._flo_num_ctrl.number

    @floor_level_num.setter
    def floor_level_num(self, value):
        if self._flo_num_ctrl.change_num(value):
            raise ValueError
        self.floor_passengers.clear()
        for i in range(1, value + 1):
            try:
                name = self.get_passenger_group_at_floor(i)
            except Exception as err:
                if type(err) is Exception and \
                        err.args == ("该方法会在加载文件后被赋值",):
                    return
                else:
                    raise err
            else:
                obj = self.passengers_groups[name]
                self.floor_passengers[i] = obj.get_start(i)

    @property
    def environment_filepath(self):
        "环境配置文件，可当作常量获取和赋值。"
        return self._env_file_btn.path

    @environment_filepath.setter
    def environment_filepath(self, val):
        cmd = self.open_environment_file(val)
        if not cmd:
            # 保存为绝对路径。
            self._env_file_btn.update_path(os.path.realpath(val))
        raise ValueError("未找到入口变量`env`")

    @property
    def elevator_speed(self):
        "电梯运行速度，单位是 秒每层 。可当作常量获取和赋值。"
        return self._ele_speed_ctrl.number

    @elevator_speed.setter
    def elevator_speed(self, value):
        if self._ele_speed_ctrl.change_num(value):
            raise ValueError("电梯速度范围错误，应属于 %s<= x < %s"
                             % self._ele_speed_ctrl.num_range)

    def open_environment_file(self, path):
        """打开环境配置文件， 但不会记录路径。
失败返回非零数值
 - 1 未找到入口变量`env`
 - 2 电梯数量过小
 - 3 电梯数量过大
 - 4 楼层数过小
 - 5 楼层数过大
 - 6 刷新时间过小
 - 7 刷新时间过大
 - 8 电梯运行速度过快
 - 9 电梯运行速度过慢
"""
        with open(path, "r", encoding="utf-8") as fp:
            file = fp.read()
        get_dict = {"Environment": Env, "Pass": Pass, "RP": RP}
        exec(file, get_dict)
        try:
            env = get_dict["env"]
        except KeyError:
            return 1
        try:
            self.elevator_num = env.elevators
        except ValueError as err:
            if err.args == (1,):
                return 2
            elif err.args == (2,):
                return 3
            else:
                raise err
        self.get_passenger_group_at_floor = env.get_passenger_group_at_floor
        self.passengers_groups.clear()
        self.passengers_groups.update(env.groups)
        try:
            self.floor_level_num = env.floors
        except ValueError as err:
            if err.args == (1,):
                return 4
            elif err.args == (2,):
                return 5
            else:
                raise err
        try:
            self.reflash_time = env.reflash_time
        except ValueError as err:
            if err.args == (1,):
                return 6
            elif err.args == (2,):
                return 7
            else:
                raise err
        try:
            self.elevator_speed = env.elevator_speed
        except ValueError as err:
            if err.args == (1,):
                return 8
            elif err.args == (2,):
                return 9
            else:
                raise err
        self.elevator_max_people = env.elevator_max
        
        self._ele_num_ctrl.changeable = env.ui_change_elevator_num
        self._ele_max_people.changeable = env.ui_change_elevator_max
        self._flo_num_ctrl.changeable = env.ui_change_floor_num
        
        self.flush_env_info_list()

    def open_strategy_file(self, path):
        """打开策略文件。
        """
        get_dict = {}

        with open(path, "r", encoding="utf-8") as fp:
            code = fp.read()
        exec(code, get_dict)

        self.Strategy = get_dict["strategy"]

    def get_passenger_group_at_floor(self, floor):
        "获取对应楼层的乘客组名称。"
        raise Exception("该方法会在加载文件后被赋值")

    def flush_env_info_list(self):
        "填充每层乘客信息表"
        self._env_info_list.delete(0, "end")
        for floor in range(1, self.floor_level_num + 1):
            text = self._get_env_info_text(floor)
            self._env_info_list.insert("end", text)

    def _get_env_info_text(self, floor):
        group = self.floor_passengers.get(floor,
                                          self.passengers_groups["nobody"])
        text = f"F{floor}".ljust(5)
        up = sum(i > floor for i in group._passenger_list)
        down = sum(i < floor for i in group._passenger_list)
        text += f"{up}↑".ljust(4) + f" {down}↓".ljust(7)

        num = sum(el.floor_to == floor for el in self.elevators)
        text += f"{num} 前往".rjust(5)
        return text

    def _env_file_cmd(self):
        """选择环境策略方案时调用的函数。
        """
        old = self.environment_filepath
        path = self._env_file_btn._cmd()  # 弹出文件选择界面，更新按钮文本
        if not path:
            return
        try:
            cmd = self.open_environment_file(path)
        except Exception as err:
            tk.messagebox.showerror("文件载入错误", repr(err))
            self._env_file_btn.update_path(old)  # 载入错误，回调
        else:
            if not cmd:
                # 保存为绝对路径。
                self._env_file_btn.update_path(os.path.realpath(path))
                return
            self._env_file_btn.update_path(old)  # 载入错误，回调
            if cmd == 1:
                tk.messagebox.showerror("文件载入错误", "未找到入口变量`env`")
            elif cmd == 2:
                tk.messagebox.showerror("文件载入错误", "电梯数量过小")
            elif cmd == 3:
                tk.messagebox.showerror("文件载入错误", "电梯数量过大")
            elif cmd == 4:
                tk.messagebox.showerror("文件载入错误", "楼层数过小")
            elif cmd == 5:
                tk.messagebox.showerror("文件载入错误", "楼层数过大")
            elif cmd == 6:
                tk.messagebox.showerror("文件载入错误", "刷新时间过小")
            elif cmd == 7:
                tk.messagebox.showerror("文件载入错误", "刷新时间过大")
            else:
                tk.messagebox.showerror("文件载入错误", f"错误代码, {cmd}")

    def _env_run_cmd(self):
        """控制模拟器执行状态时调用的函数。"""
        self._env_run_btn.click()
        if self._env_run_btn.state:
            self.thread = Thread(target=self.worker.callme, daemon=True)
            self.thread.start()
        else:
            self.thread.join()

    def _save_env_cmd(self):
        '保存编辑的环境时调用的函数。'
        path = self._save_env._cmd()
        if not path:
            return
        with open(self.ENV_TEMPLATE_PATH, "r", encoding="utf-8") as fp:
            text = fp.read()
        text += "\n".join([f'env.floors = {self.floor_level_num}',
                           f'env.elevators = {self.elevator_num}',
                           f'env.reflash_time = {self.reflash_time}',
                           f'env.elevator_max = {self.elevator_max_people}'])
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)

    def _save_str_cmd(self):
        "创建策略文件时调用的函数。"
        path = self._save_str._cmd()
        if not path:
            return
        with open(self.STR_TEMPLATE_PATH, "r", encoding="utf-8") as fp:
            text = fp.read()
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)

    def _strategy_file_cmd(self):
        "打开电梯策略时调用的函数。"
        if self.isRunning:
            ans = tk.messagebox.askokcancel("汪汪汪\N{dog}🐶🦮🐕‍🦺",
                                            "修改策略文件需要停止工作进程，继续吗？")
            if ans:
                self._env_run_btn.click()
            else:
                return
        old = self._strategy_file_btn.path
        path = self._strategy_file_btn._cmd()  # 弹出文件选择界面，更新按钮文本

        if not path:
            return

        try:
            self.open_strategy_file(path)
        except Exception as err:
            tk.messagebox.showerror("打开时策略文件时出错", repr(err))
            self._strategy_file_btn.update_path(old)  # 出错的回调

    def _ele_num_ctrl_cmd(self):
        "修改电梯数量时调用的函数。"
        self._ele_num_ctrl.num_input_cmd()
        self.elevator_num = self.elevator_num  # 神奇代码，赋值是为了更新 UI

    def _ele_speed_ctrl_cmd(self):
        "修改电梯运行速度时调用的函数。"
        old = self.elevator_speed
        self._ele_speed_ctrl.num_input_cmd()
        if old != self.elevator_speed:
            self.elevator_speed = self.elevator_speed  # 神奇代码 * 2

    def _flo_num_ctrl_cmd(self):
        "修改楼层数量时调用的函数。"
        self._flo_num_ctrl.num_input_cmd()
        self.floor_level_num = self.floor_level_num  # 神奇代码 * 3
        try:
            self.flush_env_info_list()
        except KeyError as err:
            if err.args == (1,):
                tk.messagebox.showwarning("部分失败", "无法刷新信息界面，\n"
                                                  "是否未打开环境文件")
            else:
                raise err

    def _closing(self):
        "主窗口被关闭时执行的函数"
        self._env_run_cmd()
        self._window.destroy()


class Pass:
    '''建立乘客组对象。
    _passenger_list 存储每个想去的楼层，不要乱动！
    当组被修改时， changed会被设置为 True
    进程不安全！要么给我单线程读写，要么自己加锁去（但changed可能用不到）。
    '''

    def __init__(self, name, passenger_list=None):
        self.name = name
        self._passenger_list = []
        if passenger_list:
            self._passenger_list.extend(passenger_list)
        self.changed = None

    def get_list(self):
        self.changed = False
        return tuple(self._passenger_list)

    def get_start(self, my_floor):
        ret = copy(self)
        ret.my_floor = my_floor
        while 1:
            try:
                ret._passenger_list.remove(my_floor)
            except ValueError:
                break
        return ret

    def add_a_passenger(self, want_to_floor):
        """应仅在运行时调用。向乘客组添加乘客。
        want_to_floor: int 乘客去的楼层。"""
        if want_to_floor != self.my_floor:
            self._passenger_list.append(want_to_floor)
            self.changed = True

    def add_passengers(self, passengers):
        """应仅在运行时调用。向乘客组添加乘客
        passengers: <passengers object>
        执行时会获取 passengers.get_start 属性，将返回的对象指出的乘客添加到环境中。
        """
        add = passengers.get_start(self.my_floor)
        self._passenger_list.extend(i for i in add._passenger_list
                                    if i != self.my_floor)
        self.changed = True

    def remove_passenger(self, value):
        self._passenger_list.remove(value)
        self.changed = True


class RP:
    '''随机乘客生成器，在应用时调用时会生成Passengers对象。
passenger_number: int/tuple  生成乘客总数，如果未指定整数，则应指定范围
avoid_floors    : list       会避免生成的楼层
go_up_number    : int/None   生成向上乘客的人数
go_down_number  : int/None   生成向下乘客的人数
------------------------------------------------------------------
哈哈哈哈哈因为我重载了 __new__,用户端的 __init__ 根本用不到。
    '''

    def __new__(cls, class_name, passenger_number, hi, avoid_floors=None,
                go_up_number=None, go_down_number=None):
        func = functools.partialmethod(cls.start_func, passenger_number, hi,
                                       avoid_floors,
                                       go_up_number, go_down_number)
        loc = {"get_start": func}
        for name in ("add_a_passenger", "add_passengers",
                     "call_loop", "call_elevators_stop"):
            if hasattr(cls, name): loc[name] = getattr(cls, name)
        cl = type("RandomPassengers", (Pass,), loc)
        ret = cl(class_name)
        return ret

    def start_func(self, passenger_number, hi, avoid_floors,
                   go_up_number, go_down_number, my_floor):
        if avoid_floors is None:
            avoid_floors = set()
        else:
            avoid_floors = set(avoid_floors)
        avoid_floors.add(my_floor)
        ls = []
        if isinstance(passenger_number, int):
            number = passenger_number
        else:
            number = random.randint(*passenger_number)

        def add_one_number(a, b):
            while 1:
                flo = random.randint(a, b)
                if flo not in avoid_floors:
                    ls.append(flo)
                    break

        if my_floor == hi:
            go_up_number = None
        elif my_floor == 1:
            go_down_number = None

        if go_down_number is None and go_up_number is None:
            for _ in range(number):
                add_one_number(1, hi)
        elif go_down_number is not None and go_up_number is None:
            for _ in range(go_down_number):
                add_one_number(1, my_floor - 1)
            for _ in range(number - go_down_number):
                add_one_number(my_floor + 1, hi)
        elif go_down_number is None and go_up_number is not None:
            for _ in range(go_up_number):
                add_one_number(my_floor + 1, hi)
            for _ in range(number - go_up_number):
                add_one_number(1, my_floor - 1)
        else:
            for _ in range(go_down_number):
                add_one_number(1, my_floor - 1)
            for _ in range(go_up_number):
                add_one_number(my_floor + 1, hi)

        ret = copy(self)
        ret._passenger_list = ls
        ret.my_floor = my_floor
        return ret


class Env:
    """给环境文件用于继承。但说它就是传值用的……可能之后重载`__format__`吧？
    """


class Elevator:
    colours = ["pink", "lightblue", "white", "red", "purple", "yelloW",
               "green", "gray", "coral", "lime", "gold", "royalblue",
               "fuchsia", "violet", "skyblue", "azure", "springgreen",
               "beige"]

    def __init__(self, master, number, at_floor=1):
        self.at_floor = at_floor
        self.floor_to = None
        self.start = 0  # 电梯移动楼层时间统计
        self.inside_people = []
        self.floor_from = 1  # 电梯开始移动时所在楼层
        # UI
        self.frame = tk.Frame(master, bg="silver")
        top_frame = tk.Frame(self.frame, bg="silver")
        self.title = tk.Label(top_frame, text=f"电梯 {number}",
                              bg=random.choice(self.colours))
        show_frame = tk.Frame(top_frame)
        tk.Label(show_frame, text="当前楼层").grid(column=0, row=0)
        self.label_at_floor = tk.Label(show_frame, text="1", width=5)
        self.label_at_floor.grid(column=1, row=0, sticky="w")
        tk.Label(show_frame, text="目标楼层").grid(column=0, row=1)
        self.label_to_floor = tk.Label(show_frame, text="None", width=5)
        self.label_to_floor.grid(column=1, row=1, sticky="w")
        self.label_moving_direction = tk.Label(show_frame, width="4", bg="white")
        self.label_moving_direction.grid(column=2, row=0, rowspan=2, sticky="nes")
        self.user_label = tk.Label(self.frame)
        self.passenger_frame = tk.Frame(self.frame)
        self.floor_labels = []

        self.title.pack(fill="x", side="top", pady=5)
        show_frame.pack(fill="x", side="top", pady=5)
        top_frame.pack(fill="x", side="top")
        self.user_label.pack(fill="both", side="top")
        # self.passenger_frame.pack(side="bottom", fill="y")

    @property
    def moving_direction(self):
        'up -> 1  down -> -1  nothing -> 0'
        if (self.floor_to is None) or (self.floor_to == self.at_floor):
            return 0
        elif self.floor_to < self.at_floor:
            return -1
        else:
            return 1

    def drop_off(self):
        """下客。
执行此方法会 删除电梯内前往所在楼层的乘客，并将`floor_from`定为当前楼层，并刷新UI
           但不会更改`floor_to`。"""
        while 1:
            try:
                self.inside_people.remove(self.at_floor)
            except ValueError:
                break
        self.flush_ui()

    def flush_ui(self):
        self.label_at_floor["text"] = str(self.at_floor)
        self.label_to_floor["text"] = str(self.floor_to)
        if self.moving_direction == 1:
            text = "↑"
        elif self.moving_direction == -1:
            text = "↓"
        else:
            text = ""
        self.label_moving_direction["text"] = text

        for l in self.floor_labels:
            l.pack_forget()
        self.floor_labels.clear()
        passengers = sorted(set(self.inside_people))
        for num in passengers:
            l = tk.Label(self.passenger_frame, bg="black", fg="white",
                         text=str(num).rjust(4))
            l.pack(fill="x", padx=2, pady=2)
            self.floor_labels.append(l)


class Worker:
    def __init__(self, simu: Simulation):
        self.simu = simu

        self.sta = 0

    def __enter__(self):
        self.simu.isRunning = True

    def __exit__(self, *args):
        self.simu.isRunning = False
        if self.simu._env_run_btn.state is True:  # 说明并不是因为按钮而结束程序的
            tk.messagebox.showerror("错误", "工作线程意外结束\n%s\n%s\n%s" % args)
        self.simu._env_run_btn.to_state(False)

    def callme(self):
        with self:
            loop_time = time.time()
            while 1:
                sta = time.time()
                self.loop(loop_time)
                try:
                    time.sleep(self.simu.reflash_time - time.time() + sta)
                except ValueError:
                    pass
                loop_time += self.simu.reflash_time

    def loop(self, this_loop_time):
        '''
        需加载与更新：
        - 刷新速度 (reflash_time)
        - 楼层数
        - 电梯数 (elevator_num)
        - 人数方案组
        - 每层的人数方案
        - 每层的人数状态 (_env_info_list)
        - 根据接口动态更新人数方案 (call_loop & call_elevators_stop)
        - 修改进程状态指 (isRunning)
        - 电梯运行速度 (elevator_speed)'''
        if not self.simu._env_run_btn.state:
            sys.exit()
        if any(i.changed for i in self.simu.floor_passengers.values()):
            self.simu.flush_env_info_list()
        elevator_stopped = self.flush_elevators(this_loop_time)

        # run 决策文件
        send = {"say": "routine",
                "arrive elevator": elevator_stopped}
        run = bool(elevator_stopped)
        while run:
            send.update(self.get_kargs())
            msg = self.simu.Strategy.elevator_arrive_call(send)
            if msg["cmd"] == "bye":
                break
            send = self.read_message(msg, this_loop_time)
            send["arrive elevator"] = elevator_stopped

        send = {"say": "routine"}
        while 1:
            send.update(self.get_kargs())
            msg = self.simu.Strategy.loop_call(send)
            if msg["cmd"] == "bye":
                break
            send = self.read_message(msg, this_loop_time)
        # run 楼层刷新函数
        for p in self.simu.floor_passengers.values():
            if elevator_stopped and hasattr(p, "call_elevators_stop"):
                p.call_elevators_stop(elevator_stopped)
            if hasattr(p, "call_loop"):
                p.call_loop()

    def flush_elevators(self, this_loop_time):
        """刷新电梯，返回的列表元素依次为
“到达的电梯”的序号、所在楼层、上次停靠楼层、每个乘客目标元组
"""
        rst = []
        for i, e in enumerate(self.simu.elevators):
            if e.floor_to and \
                    (this_loop_time - e.start) > self.simu.elevator_speed:
                # 电梯有执行目标
                e.at_floor += e.moving_direction  # 移动
                e.start = this_loop_time
                if e.moving_direction:
                    # 说明电梯未到达目标
                    e.flush_ui()
                    continue
                # --到达目标楼层的电梯才执行--
                e.floor_to = None
                e.drop_off()  # 已到达电梯下客
                add = i, e.at_floor, e.floor_from, tuple(e.inside_people)
                rst.append(add)  # 添加到返回列表中
        return rst

    def get_kargs(self):
        return {"passenger": {k: v.get_list()
                              for k, v in self.simu.floor_passengers.items()},
                "elevator": [(e.at_floor, e.floor_to, e.moving_direction)
                             for e in self.simu.elevators]}

    def read_message(self, msg, this_loop_time):
        cmd = msg["cmd"]
        if cmd == "elevator to":
            # 设置电梯
            to_floor = msg["F"]
            index = msg["N"]
            e = self.simu.elevators[index]
            e.floor_to = to_floor
            e.start = this_loop_time
            e.floor_from = e.at_floor
            e.flush_ui()
            return {"say": "success", "return": tuple(e.inside_people),
                    "last command": msg}
        elif cmd == "elevator up":
            # 上客
            index = msg["N"]
            e = self.simu.elevators[index]
            d = 1
            at = e.at_floor
            pop = [i for i in self.simu.floor_passengers[at].get_list()
                   if (i - at) * d > 0]
            max_abord = self.simu.elevator_max_people - len(e.inside_people)
            k = min(len(pop), max_abord)
            passengers = random.sample(pop, k)
            e.inside_people.extend(passengers)
            for p in passengers:
                self.simu.floor_passengers[at].remove_passenger(p)
            e.flush_ui()
            self.simu.flush_env_info_list()
            return {"say": "success", "return": tuple(e.inside_people),
                    "last command": msg}
        elif cmd == "elevator down":
            # 上客
            index = msg["N"]
            e = self.simu.elevators[index]
            d = -1
            at = e.at_floor
            pop = [i for i in self.simu.floor_passengers[at].get_list()
                   if (i - at) * d > 0]
            max_abord = self.simu.elevator_max_people - len(e.inside_people)
            k = min(len(pop), max_abord)
            passengers = random.sample(pop, k)
            e.inside_people.extend(passengers)
            for p in passengers:
                self.simu.floor_passengers[at].remove_passenger(p)
            e.flush_ui()
            self.simu.flush_env_info_list()
            return {"say": "success", "return": tuple(e.inside_people),
                    "last command": msg}
        elif cmd == "passengers in elevator":
            index = msg["N"]
            e = self.simu.elevators[index]
            return {"say": "success", "return": tuple(e.inside_people),
                    "last command": msg}
        elif cmd == "label config update":
            index = msg["N"]
            data = msg["data"]
            self.simu.elevators[index].user_label.config(**data)
            return {"say": "success", "return": None,
                    "last command": msg}
        else:
            return {"say": "error", "error": "unknow command",
                    "last command": msg}


sln = Simulation()

sln.mainloop()

sys.exit()
