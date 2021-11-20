UP = 2
DOWN = 1
NONE = 0


# 请求类
class Request:
    def __init__(self, floor: int, dir: int):
        # 发送请求的楼层
        self.floor = floor
        # 请求的方向
        self.dir = dir

    def __gt__(self, b):
        return self.floor > b.floor

    def __lt__(self, b):
        return self.floor < b.floor
    def __repr__(self):
        return f"Request({self.floor}, {self.dir})"


# 请求队列插入
# 参数 请求队列 当前楼层 请求
def insert(queue, floor: int, req: Request):
    length = len(queue)
    # 队列空时不需要排序
    if length == 0:
        return queue.append(req)

    # 计算方向
    if (floor - queue[0].floor) > 0:
        dir = DOWN
    elif (floor - queue[0].floor) < 0:
        dir = UP
    else:
        dir = NONE
        print("fuck")
        # 注意这种情况. 到达了楼层应当先出队
        pass

    positive_queue = []  # 相同方向路径请求
    negative_queue = []  # 相反方向路径请求
    positive_queue_passed = []  # 相同方向已经过路径请求

    if req.dir == NONE:
        req.dir = dir

    queue.append(req)

    for i in queue:
        if dir == UP:
            if i.dir == dir and i.floor > floor:
                positive_queue.append(i)
            elif i.dir == dir and i.floor < floor:
                positive_queue_passed.append(i)
            elif i.dir != dir:
                negative_queue.append(i)
            else:
                print("fuck")
        elif dir == DOWN:
            if i.dir == dir and i.floor < floor:
                positive_queue.append(i)
            elif i.dir == dir and i.floor > floor:
                positive_queue_passed.append(i)
            elif i.dir != dir:
                negative_queue.append(i)
            else:
                print("fuck")
        else:
            print("fuck")

    positive_queue = sorted(positive_queue)
    positive_queue_passed = sorted(positive_queue_passed)
    negative_queue = sorted(negative_queue)

    if dir == UP:
        negative_queue.reverse()
        queue = positive_queue + negative_queue + positive_queue_passed
    elif dir == DOWN:
        positive_queue.reverse()
        positive_queue_passed.reverse()
        queue = positive_queue + negative_queue + positive_queue_passed
    else:
        print("fuck")

    return queue


priority_queue = []
current_floor = 1
while True:
    # 输入格式 楼层 空格 (0到楼层/1下/2上)
    # 输出格式 自己开debug看
    data = input(":")
    data = data.split(" ")
    insert(priority_queue, current_floor, Request(int(data[0]), int(data[1])))
    print("ok")
