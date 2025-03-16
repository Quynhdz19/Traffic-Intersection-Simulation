import random
import time
import threading
import pygame
import sys
from collections import deque

# Cấu hình chung
noOfSignals = 4
speeds = {'car': 2.25, 'bus': 1.8, 'truck': 1.8, 'bike': 2.5}
minGreen = 5
maxGreen = 40
defaultYellow = 5
defaultRed = 150

# Biến toàn cục cho hai mô phỏng
signals_left = []  # Bên trái (không tối ưu)
signals_right = []  # Bên phải (đã tối ưu)
currentGreen_left = 0
currentGreen_right = 0
nextGreen_left = (currentGreen_left + 1) % noOfSignals
nextGreen_right = (currentGreen_right + 1) % noOfSignals
currentYellow_left = 0
currentYellow_right = 0

# Cấu hình giao lộ
x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}

# Dữ liệu xe cho hai mô phỏng
vehicles_left = {'right': {0: deque(), 1: deque(), 2: deque(), 'crossed': 0, 'waiting': 0},
                 'down': {0: deque(), 1: deque(), 2: deque(), 'crossed': 0, 'waiting': 0},
                 'left': {0: deque(), 1: deque(), 2: deque(), 'crossed': 0, 'waiting': 0},
                 'up': {0: deque(), 1: deque(), 2: deque(), 'crossed': 0, 'waiting': 0}}
vehicles_right = {'right': {0: deque(), 1: deque(), 2: deque(), 'crossed': 0, 'waiting': 0},
                  'down': {0: deque(), 1: deque(), 2: deque(), 'crossed': 0, 'waiting': 0},
                  'left': {0: deque(), 1: deque(), 2: deque(), 'crossed': 0, 'waiting': 0},
                  'up': {0: deque(), 1: deque(), 2: deque(), 'crossed': 0, 'waiting': 0}}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

stoppingGap = 15
movingGap = 15

pygame.init()
simulation_left = pygame.sprite.Group()
simulation_right = pygame.sprite.Group()


class TrafficSignal:
    def __init__(self, red, yellow, green, optimized=False):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""
        self.optimized = optimized

    def calculate_green_time(self, vehicles_data):
        if not self.optimized:
            return 10  # Thời gian cố định cho bên trái (không tối ưu)
        direction = directionNumbers[signals_right.index(self)]
        vehicle_count = sum(len(vehicles_data[direction][lane]) for lane in range(3))
        green_time = min(maxGreen, max(minGreen, vehicle_count * 2))  # 2 giây/xe
        return green_time


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, is_left=True):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        vehicles = vehicles_left if is_left else vehicles_right
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)

        if self.index > 0 and vehicles[direction][lane][self.index - 1].crossed == 0:
            prev_vehicle = vehicles[direction][lane][self.index - 1]
            if direction == 'right':
                self.stop = prev_vehicle.stop - prev_vehicle.image.get_rect().width - stoppingGap
            elif direction == 'left':
                self.stop = prev_vehicle.stop + prev_vehicle.image.get_rect().width + stoppingGap
            elif direction == 'down':
                self.stop = prev_vehicle.stop - prev_vehicle.image.get_rect().height - stoppingGap
            elif direction == 'up':
                self.stop = prev_vehicle.stop + prev_vehicle.image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]

        temp = self.image.get_rect().width if direction in ['right', 'left'] else self.image.get_rect().height
        temp += stoppingGap
        if direction == 'right':
            x[direction][lane] -= temp
        elif direction == 'left':
            x[direction][lane] += temp
        elif direction == 'down':
            y[direction][lane] -= temp
        elif direction == 'up':
            y[direction][lane] += temp

        if is_left:
            simulation_left.add(self)
        else:
            simulation_right.add(self)

    def move(self, is_left=True):
        global currentGreen_left, currentGreen_right, currentYellow_left, currentYellow_right
        vehicles = vehicles_left if is_left else vehicles_right
        currentGreen = currentGreen_left if is_left else currentGreen_right
        currentYellow = currentYellow_left if is_left else currentYellow_right

        direction = self.direction
        if direction == 'right':
            if self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[direction]:
                self.crossed = 1
                vehicles[direction]['crossed'] += 1
                vehicles[direction]['waiting'] = max(0, vehicles[direction]['waiting'] - 1)
            if self.crossed == 0 and self.x < stopLines[direction]:
                vehicles[direction]['waiting'] += 1
            if (self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or
                (currentGreen == 0 and currentYellow == 0)) and \
                    (self.index == 0 or self.x + self.image.get_rect().width <
                     (vehicles[direction][self.lane][self.index - 1].x - movingGap)):
                self.x += self.speed
        # Tương tự cho các hướng khác (down, left, up)
        elif direction == 'down':
            if self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[direction]:
                self.crossed = 1
                vehicles[direction]['crossed'] += 1
                vehicles[direction]['waiting'] = max(0, vehicles[direction]['waiting'] - 1)
            if self.crossed == 0 and self.y < stopLines[direction]:
                vehicles[direction]['waiting'] += 1
            if (self.y + self.image.get_rect().height <= self.stop or self.crossed == 1 or
                (currentGreen == 1 and currentYellow == 0)) and \
                    (self.index == 0 or self.y + self.image.get_rect().height <
                     (vehicles[direction][self.lane][self.index - 1].y - movingGap)):
                self.y += self.speed
        elif direction == 'left':
            if self.crossed == 0 and self.x < stopLines[direction]:
                self.crossed = 1
                vehicles[direction]['crossed'] += 1
                vehicles[direction]['waiting'] = max(0, vehicles[direction]['waiting'] - 1)
            if self.crossed == 0 and self.x > stopLines[direction]:
                vehicles[direction]['waiting'] += 1
            if (self.x >= self.stop or self.crossed == 1 or
                (currentGreen == 2 and currentYellow == 0)) and \
                    (self.index == 0 or self.x >
                     (vehicles[direction][self.lane][self.index - 1].x + vehicles[direction][self.lane][
                         self.index - 1].image.get_rect().width + movingGap)):
                self.x -= self.speed
        elif direction == 'up':
            if self.crossed == 0 and self.y < stopLines[direction]:
                self.crossed = 1
                vehicles[direction]['crossed'] += 1
                vehicles[direction]['waiting'] = max(0, vehicles[direction]['waiting'] - 1)
            if self.crossed == 0 and self.y > stopLines[direction]:
                vehicles[direction]['waiting'] += 1
            if (self.y >= self.stop or self.crossed == 1 or
                (currentGreen == 3 and currentYellow == 0)) and \
                    (self.index == 0 or self.y >
                     (vehicles[direction][self.lane][self.index - 1].y + vehicles[direction][self.lane][
                         self.index - 1].image.get_rect().height + movingGap)):
                self.y -= self.speed


def initialize_left():
    ts1 = TrafficSignal(0, defaultYellow, minGreen, optimized=False)
    signals_left.append(ts1)
    ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, defaultYellow, minGreen, optimized=False)
    signals_left.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, minGreen, optimized=False)
    signals_left.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, minGreen, optimized=False)
    signals_left.append(ts4)
    repeat_left()


def initialize_right():
    ts1 = TrafficSignal(0, defaultYellow, minGreen, optimized=True)
    signals_right.append(ts1)
    ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, defaultYellow, minGreen, optimized=True)
    signals_right.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, minGreen, optimized=True)
    signals_right.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, minGreen, optimized=True)
    signals_right.append(ts4)
    repeat_right()


def repeat_left():
    global currentGreen_left, currentYellow_left, nextGreen_left
    while True:
        signals_left[currentGreen_left].green = signals_left[currentGreen_left].calculate_green_time(vehicles_left)
        while signals_left[currentGreen_left].green > 0:
            updateValues_left()
            time.sleep(1)
        currentYellow_left = 1
        for i in range(3):
            for vehicle in vehicles_left[directionNumbers[currentGreen_left]][i]:
                vehicle.stop = defaultStop[directionNumbers[currentGreen_left]]
        while signals_left[currentGreen_left].yellow > 0:
            updateValues_left()
            time.sleep(1)
        currentYellow_left = 0
        signals_left[currentGreen_left].yellow = defaultYellow
        signals_left[currentGreen_left].red = defaultRed
        currentGreen_left = nextGreen_left
        nextGreen_left = (currentGreen_left + 1) % noOfSignals
        signals_left[nextGreen_left].red = signals_left[currentGreen_left].yellow + signals_left[
            currentGreen_left].green


def repeat_right():
    global currentGreen_right, currentYellow_right, nextGreen_right
    while True:
        signals_right[currentGreen_right].green = signals_right[currentGreen_right].calculate_green_time(vehicles_right)
        while signals_right[currentGreen_right].green > 0:
            updateValues_right()
            time.sleep(1)
        currentYellow_right = 1
        for i in range(3):
            for vehicle in vehicles_right[directionNumbers[currentGreen_right]][i]:
                vehicle.stop = defaultStop[directionNumbers[currentGreen_right]]
        while signals_right[currentGreen_right].yellow > 0:
            updateValues_right()
            time.sleep(1)
        currentYellow_right = 0
        signals_right[currentGreen_right].yellow = defaultYellow
        signals_right[currentGreen_right].red = defaultRed
        currentGreen_right = nextGreen_right
        nextGreen_right = (currentGreen_right + 1) % noOfSignals
        signals_right[nextGreen_right].red = signals_right[currentGreen_right].yellow + signals_right[
            currentGreen_right].green


def updateValues_left():
    for i in range(noOfSignals):
        if i == currentGreen_left:
            if currentYellow_left == 0:
                signals_left[i].green -= 1
            else:
                signals_left[i].yellow -= 1
        else:
            signals_left[i].red -= 1


def updateValues_right():
    for i in range(noOfSignals):
        if i == currentGreen_right:
            if currentYellow_right == 0:
                signals_right[i].green -= 1
            else:
                signals_right[i].yellow -= 1
        else:
            signals_right[i].red -= 1


def generateVehicles_left():
    while True:
        vehicle_type = random.randint(0, 3)
        lane_number = random.randint(0, 2)
        direction_number = random.randint(0, 3)
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number],
                is_left=True)
        time.sleep(0.2)  # Xe xuất hiện dồn dập để gây tắc đường


def generateVehicles_right():
    while True:
        vehicle_type = random.randint(0, 3)
        lane_number = random.randint(0, 2)
        direction_number = random.randint(0, 3)
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number],
                is_left=False)
        time.sleep(0.2)


class Main:
    thread1 = threading.Thread(name="init_left", target=initialize_left, args=())
    thread1.daemon = True
    thread1.start()

    thread2 = threading.Thread(name="init_right", target=initialize_right, args=())
    thread2.daemon = True
    thread2.start()

    black = (0, 0, 0)
    white = (255, 255, 255)
    screenWidth = 2800  # Gấp đôi chiều rộng để chia 2 màn hình
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)
    background = pygame.image.load('images/intersection.png')
    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("TRAFFIC SIMULATION: LEFT (JAM) | RIGHT (OPTIMIZED)")

    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    thread3 = threading.Thread(name="generate_left", target=generateVehicles_left, args=())
    thread3.daemon = True
    thread3.start()

    thread4 = threading.Thread(name="generate_right", target=generateVehicles_right, args=())
    thread4.daemon = True
    thread4.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        # Màn hình bên trái (không tối ưu)
        screen.blit(background, (0, 0))
        for i in range(noOfSignals):
            if i == currentGreen_left:
                if currentYellow_left == 1:
                    signals_left[i].signalText = signals_left[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signals_left[i].signalText = signals_left[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                signals_left[i].signalText = signals_left[i].red if signals_left[i].red <= 10 else "---"
                screen.blit(redSignal, signalCoods[i])
        for i in range(noOfSignals):
            signalTexts = font.render(str(signals_left[i].signalText), True, white, black)
            screen.blit(signalTexts, signalTimerCoods[i])
        for vehicle in simulation_left:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move(is_left=True)

        # Màn hình bên phải (tối ưu)
        screen.blit(background, (1400, 0))
        for i in range(noOfSignals):
            if i == currentGreen_right:
                if currentYellow_right == 1:
                    signals_right[i].signalText = signals_right[i].yellow
                    screen.blit(yellowSignal, (signalCoods[i][0] + 1400, signalCoods[i][1]))
                else:
                    signals_right[i].signalText = signals_right[i].green
                    screen.blit(greenSignal, (signalCoods[i][0] + 1400, signalCoods[i][1]))
            else:
                signals_right[i].signalText = signals_right[i].red if signals_right[i].red <= 10 else "---"
                screen.blit(redSignal, (signalCoods[i][0] + 1400, signalCoods[i][1]))
        for i in range(noOfSignals):
            signalTexts = font.render(str(signals_right[i].signalText), True, white, black)
            screen.blit(signalTexts, (signalTimerCoods[i][0] + 1400, signalTimerCoods[i][1]))
        for vehicle in simulation_right:
            screen.blit(vehicle.image, [vehicle.x + 1400, vehicle.y])
            vehicle.move(is_left=False)

        # Tiêu đề
        left_title = font.render("Traffic Jam (Fixed Timing)", True, (255, 0, 0), black)
        right_title = font.render("Optimized (Adaptive Timing)", True, (0, 255, 0), black)
        screen.blit(left_title, (screenWidth // 4 - 100, 20))
        screen.blit(right_title, (3 * screenWidth // 4 - 100, 20))

        pygame.display.update()


if __name__ == "__main__":
    Main()