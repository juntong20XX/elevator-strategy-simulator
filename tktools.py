#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 14 23:42:06 2021

@author: Juntong.Zhu21
"""
import tkinter as tk
import tkinter.messagebox
import tkinter.simpledialog
import tkinter.filedialog
import os, itertools


class TextNumPanedWindow(tk.PanedWindow):
    def __init__(self, master, text, num=None, num_range=(0, 200), isint=False, changeable=True,
                 **kw):
        "数值范围为左闭右开区间"
        d = {"orient": "horizontal"}
        d.update(kw)
        super().__init__(master, **d)
        self.left_text = tk.Label(self, text=text)
        self.right_num = tk.Button(self, command=self.num_input_cmd,
                                   text=str(num_range[1]))
        self.num_range = num_range
        self.isint = isint
        if num is None:
            num = num_range[0]
        if self.change_num(num):
            raise ValueError("num out of range!")
        self.add(self.left_text, minsize=self.left_text.winfo_reqwidth() // 2)
        self.add(self.right_num, minsize=self.right_num.winfo_reqwidth() // 2)
        
        self.changeable = changeable

    def num_input_cmd(self):
        text = "请输入数字，范围 [{}, {})".format(*self.num_range)
        if self.isint:
            num = tk.simpledialog.askinteger(self.left_text["text"], text,
                                             initialvalue=self.right_num["text"])
        else:
            num = tk.simpledialog.askfloat(self.left_text["text"], text,
                                           initialvalue=self.right_num["text"])
        if num is None:
            return
        rst = self.change_num(num)
        if rst:
            tk.messagebox.showerror("错误", "数字范围错误")
            self.num_input_cmd()

    def change_num(self, num):
        "修改数字值，成功返回 0，数值过大返回1，过小返回2。"
        if num < self.num_range[0]:
            return 1
        if num >= self.num_range[1]:
            return 2
        self.right_num["text"] = str(num)
        self.number = num
    @property
    def changeable(self):
        return self.right_num.cget("state") == "normal"
    @changeable.setter
    def changeable(self, value):
        value = bool(value)
        if self.changeable == value:
            return
        state = "normal" if value else "disable"
        self.right_num.config(state = state)


class NumButton(tk.Button):
    def __init__(self, master, isint=False, num_range=None, num=None, **kw):
        "数值范围为左闭右开区间，可以为None"
        d = {"text": "0", "command": self.num_input_cmd}
        d.update(kw)
        self.isint = isint
        self.num_range = num_range
        if not num:
            if not num_range:
                num = 0
            else:
                num = num_range[0]
        super().__init__(master, **d)
        self.change_num(num)

    def num_input_cmd(self):
        text = "请输入数字"
        if self.num_range:
            text += "，范围 [{}, {})".format(*self.num_range)
        askinteger = tk.simpledialog.askinteger
        askfloat = tk.simpledialog.askfloat
        func = askinteger if self.isint else askfloat
        num = func(text, text, initialvalue=self["text"])
        if num is None:
            return
        rst = self.change_num(num)
        if rst:
            tk.messagebox.showerror("错误", "数字范围错误")
            self.num_input_cmd()

    def change_num(self, num):
        "修改数字值，成功返回 0，数值过大返回1，过小返回2。"
        if self.num_range:
            if num < self.num_range[0]:
                return 1
            if num >= self.num_range[1]:
                return 2
        func = int if self.isint else float
        self.number = func(num)
        self["text"] = str(self.number)
        return 0


class FileButton(tk.Button):
    def __init__(self, master, path=None, issave=False,
                 change_text_with_path=False, **kw):
        d = {"command": self._cmd}
        d.update(kw)
        self.path = path
        self.issave = issave
        self.change_text_with_path = change_text_with_path
        if change_text_with_path and d.get("text") is None:
            d["text"] = os.path.basename(path)
        super().__init__(master, **d)

    def _cmd(self):
        func = tk.filedialog.asksaveasfilename if self.issave else tk.filedialog.askopenfilename
        self.path = path = func()
        if not path:
            return
        if self.change_text_with_path:
            self["text"] = os.path.basename(path)
        return path

    def update_path(self, path):
        "其实就是`self.path=path`，不过是当选择按钮文本和路径同步时，会修改文本。"
        if self.change_text_with_path:
            self["text"] = os.path.basename(str(path))
        self.path = path


class Switch(tk.Button):
    """继承自 tkinter 的按钮，自带command可在a、b两个状态切换。
属性 state : bool , False if switch in state a, True in state b."""
    def __init__(self, master, text, text_b, bg, bg_b, **kw):
        d = {"command": self.click}
        d.update(kw)
        super().__init__(master, text=text, bg=bg, **d)
        self.text_a = text
        self.bg_a = bg
        self.bg_b = bg_b
        self.text_b = text_b
        self.state = False

    def click(self):
        if self.state:
            self["text"] = self.text_a
            self["bg"] = self.bg_a
        else:
            self["text"] = self.text_b
            self["bg"] = self.bg_b
        self.state = not self.state

    def to_state(self, state):
        if self.state == state:
            return
        else:
            self.click()


class ChangeButton(tk.Button):
    """类似上面定义的`Switch`, 该类型可以在数个状态间切换。
    ls 应为可迭代对象, 其元素为该状态时按钮的配置。
    若 add_index 为 True, 则会利用 `enumerate` 为 ls各个元素添加索引, 供改变状态时
刷新 index 属性。"""
    def __init__(self, master, ls, init_config=None, add_index=True):
        if add_index:
            ls = enumerate(ls)
        self.lsconfig = itertools.cycle(ls)
        if not init_config:
            init_config = {}
        init_cfg = {"command": self.next_update}
        init_cfg.update(init_config)
        super().__init__(master, **init_cfg)
        self.next_update()
    def next_update(self):
        self.index, kw = next(self.lsconfig)
        self.config(**kw)
