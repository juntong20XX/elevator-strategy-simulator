# 电梯算法模拟器

## 简介

​		这是一个2021未来城市计划黑客马拉松参赛项目，用于创建图形界面模拟环境来测试电梯执行策略。该模拟器可以实时显示电梯的状态，动态增减呼梯乘客，并支持动态增加楼层、电梯数量等。

## 使用方法

​		运行` simulation.py`打开图形界面。选择并打开环境文件和策略模板。点击“点击执行”按钮即可运行。可以点击“创建环境文件”和“创建策略文件”，从模板生成文件。

​		环境文件和策略文件的用法详见模板的注释。

## Demo

​		有环境示例`env_example.py`和策略示例`strategy_example.py`。该策略示例支持动态增减楼层和电梯数。

## 更新说明

版本：(2021-12-8，夜间更新)

1. 修改了策略函数标准传入值 `info["elevator"]` 。该列表的元素增加了一个整数值表示该电梯的最大载客量。
2. 按照`PyCharm`的提示格式化了环境、策略模板。
3. 重写了策略示例，新的策略示例仍支持动态增减电梯数、电梯最大载客数；且代码更加优雅，策略分配更加合理。

## TODO

​		修改显示区域“电梯前往”错误的 bug。

​		添加重置电梯数据功能。

​		在展示界面显示电梯内人数。

​		添加版本系统。

​		<font color="red">已放弃，下一次更新删去此内容</font><font color="gray">将电梯策略操作改为协程操作，不确定是否要向下兼容性。</font><font color="red">放弃原因：对原有代码的修改较大，且可在策略文件自定义类似操作</font>
