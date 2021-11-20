#!/usr/bin/env python3
# -*- coding: utf-8 -*-
class Passengers(locals()["Pass"]):
    '''建立乘客组对象。
passenger_list: interable  元素类型为 int ，代表一名去对应楼层的乘客

可继承该对象，添加方法以调用的接口：
func call_loop() #每个周期调用一次，注意控制运算时间。
func call_elevators_stop(elevator_info:list) #当有电梯到达目标楼层时触发
        #[(电梯的编号:int,
           该电梯所在楼层:int,
           该电梯上一个停靠楼层:int,
           电梯内每个乘客目标楼层:tuple
           ), ...]
    '''
    def __init__(self, name, passenger_list=None):
        super().__init__(name, passenger_list)
    def get_start(self, my_floor):
        """系统内部挂载楼层时调用的接口，可以重写以实现复杂方法。
    返回Passengers对象，
    默认为自己的复制，并向该复制添加 my_floor 常量，代表被设置到的楼层。
    自动删除前往当前楼层的乘客。
"""
        return super().get_start(my_floor)
    def add_a_passenger(self, want_to_floor):
        """向乘客组添加乘客。应**仅**用于运行时动态增加乘客。
        want_to_floor: int 乘客去的楼层。"""
        super().add_a_passenger(want_to_floor)
    def add_passengers(self, passengers):
        """向乘客组添加多个乘客。应**仅**用于运行时动态增加乘客。
        passengers: <passengers object>
        执行时会获取 passengers.get_start 属性，将返回的对象指出的乘客添加到环境中。
        """
        super().add_passengers(passengers)

class random_passenger(locals()["RP"]):
    '''随机乘客生成器，在应用时调用时会生成Passengers对象。
支持所有Passengers功能以及功能重写。
passenger_number: int/tuple  生成乘客总数，如果未指定整数，则应指定范围（闭区间）
hi              : int        楼层最高值，可填入楼层数
avoid_floors    : set        会避免生成的楼层，自动添加被挂载的楼层
go_up_number    : int/None   生成向上乘客的人数，处在最高层时自动失效
go_down_number  : int/None   生成向下乘客的人数，处在1层时自动失效
============================================================
请注意： 该方法不进行输入检查。
如果输入有误可能遇到一些问题：
 - "avoid_floors"包含了全部楼层生成选择， 会导致**死循环**
 - "go_up_number"和"go_down_number"均被指定时会导致"passenger_number"失效
    '''
    def __init__(self, name, passenger_number, hi, avoid_floors=None,
                 go_up_number=None, go_down_number=None):
        pass



class Environment(locals()["Environment"]):
    '''将环境配置填写在实例化的`env`中。
名称           类型    含义                默认值    范围
=====          =====  =====               ====     ====
floors         int    总楼层数               10     1 <= x <= 999
elevators      int    电梯数量                1     1 <= x <= 30
elevator_speed float  电梯运行时间            1     0 <= x < 60
elevator_max   int    电梯最大载客数         10     2 <= x < 20
reflash_time   float  刷新时间              0.1     0.01 <= x < 10
groups         dict   乘客组列表，不建议碰    {}     {str: <passengers object>}
pass_floor     dict   每层的乘客组           {}     {int: str}
    '''
    def __init__(self):
        self.floors = 10
        self.elevators = 1
        self.elevator_speed = 1
        self.elevator_max = 10
        self.reflash_time = 0.1
        self.groups = {"nobody": Passengers("nobody")}
        self.pass_floor = {}
    def add_group(self, obj):
        "将此乘客组登记到接口列表上。"
        if obj.name in self.groups:
            raise ValueError("乘客组名称重复")
        self.groups[obj.name] = obj
    def get_passenger_group_at_floor(self, floor):
        "系统内部使用，可重写，获取对应楼层的乘客组名称。"#写在这里用来展示默认情况
        return self.pass_floor.get(floor, "nobody")


env = Environment()#这个是唯一被检索的入口变量。
