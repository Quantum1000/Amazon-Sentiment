import numpy as np

lightstates = ['red', 'off']
dirnames = ['north', 'east', 'south', 'west']
directions = {'N':0, 'E':1, 'S':2, 'W':3}
lightnames = ['left arrow', 'light']
turns = {'left':1, 'straight':2}
class Car:
    def __init__(self, cararr):
        self.time = int(cararr[0])
        self.dir = directions[cararr[1].strip()]
        string = cararr[2].strip()
        self.turn = turns[string]
    time = 0
    direct = 0
    turn = 2
# Which test case to run:
fp = open('INPUT.txt', 'r')
lines = fp.readlines()
fp.close()
carslist = []
for line in lines:
    carArr = line.split(' ')
    carslist.append(Car(carArr))

class simulation:
    def __init__(self, cars):
        self.cars = cars
        self.lights = [[0,0],[0,0],[0,0],[0,0]]
        self.lanes = [[[],[]],[[],[]],[[],[]],[[],[]]]
        self.time = 0
    lights = [[0,0],[0,0],[0,0],[0,0]]
    lanes = [[[],[]],[[],[]],[[],[]],[[],[]]]
    cars = []
    time = 0
    def addCar(self, car):
        self.lanes[car.dir][car.turn - 1].insert(0, car)
    def simulate(self, n):
        for i in range(n):
            # check for 2 lanes that can both go, pick the lanes with the most cars
            message = ''
            newlights = [[0,0],[0,0],[0,0],[0,0]]
            maxpos = 0
            maxval = 0
            for j in range(4):
                thisval = min(len(self.lanes[j][1]), len(self.lanes[(j+1)%4][0]))
                if thisval > maxval:
                    maxpos = j
                    maxval = thisval
            if maxval > 0:
                newlights[maxpos][1] = 1
                newlights[(maxpos+1)%4][0] = 1
                self.lanes[maxpos][1].pop()
                self.lanes[(maxpos+1)%4][0].pop()
                message = '2 cars went ' + dirnames[(maxpos+2)%4] + '.'
            else:
                maxj = 0
                maxk = 0
                maxval = 0
                for j in range(4):
                    for k in range(2):
                        thisval = len(self.lanes[j][k])
                        if thisval > maxval:
                            maxj = j
                            maxk = k
                            maxval = thisval
                if maxval > 0:
                    newlights[maxj][maxk] = 1
                    self.lanes[maxj][maxk].pop()
                    message = '1 car went ' + dirnames[(maxj+2)%4] + '.'
                else:
                    message = '0 cars went through the intersection.'
            for j in range(4):
                for k in range(2):
                    if self.lights[j][k] != newlights[j][k]:
                        print('The ' + dirnames[j] + ' ' +  lightnames[k] + ' is now ' + lightstates[newlights[j][k]] + '.')
            print('Time ' + str(self.time) + ', ' + message)
            self.time = self.time + 1
            self.lights = newlights
sim = simulation(carslist)
for car in carslist:
    sim.simulate(car.time-sim.time)
    sim.addCar(car)
def carsWaiting():
    for j in range(4):
        for k in range(2):
            if len(sim.lanes[j][k]) > 0:
                return True
    return False
while carsWaiting():
    sim.simulate(1)