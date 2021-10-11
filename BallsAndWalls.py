"""Provides a Balls class(subclass of Circles) and Walls class(subclass of AABBs.

Balls class are the 2d balls used in the maxwell's demon game. Note that we simulate them
as 2d rigid circles with collision, instead of particles with repulsion.
Also Provides a function for generating random initial ball positions and directions.
Balls are initialized with arguments passed, while walls are initialized as the actual 
game display.
"""

import taichi as ti
from Rigid2dBody import Circles, AABBs
from random import random
import math

__author__ = "507C"
__credits__ = ["507C", "Y7K4"]
__version__ = "1.0.1"
__maintainer__ = "507C"

'''
2d balls for the maxwell's demon game. Each object represent a group of balls.
'''
@ti.data_oriented
class Balls(Circles):
    def __init__(self, N, mass, pos_x, pos_y, theta, radius, init_speed, elasticity) -> None:
        pos = ti.Vector.field(2, ti.f32, shape=N)
        vel = ti.Vector.field(2, ti.f32, shape=N)
        for i in range(N):
            pos[i] = ti.Vector([pos_x[i], pos_y[i]])
            vel[i] = ti.Vector([ti.cos(theta[i]), ti.sin(theta[i])]) * init_speed
        super().__init__(N, mass, pos, radius, elasticity, vel)

    '''
    True if all balls are in the given area(either left half or right half).
    '''
    def detect_success(self, left=True):
        for i in range(self.n):
            if left and self.pos[i][0] + self.radius > 0.5:
                return False
            if not left and self.pos[i][0] - self.radius < 0.5:
                return False
        return True

    '''
    The number of balls in the given area(either left half or right half).
    '''
    def success_ball_number(self, left=True):
        num = 0
        for i in range(self.n):
            if left and self.pos[i][0] + self.radius < 0.5:
                num += 1
            if not left and self.pos[i][0] - self.radius > 0.5:
                num += 1
        return num

    '''
    Calculate kinetic energy. Help with testing, not used in game itself.
    '''
    @ti.kernel
    def get_kinetic_energy(self) -> ti.f32:
        k = 0.0
        for i in range(self.n):
            k += self.mass * self.vel[i].norm() ** 2
        k /= 2.0
        return k

    '''
    Calculate momentum x dir. Help with testing, not used in game itself.
    '''
    @ti.kernel
    def get_momentum_x(self) -> ti.f32:
        p = ti.Vector([0.0, 0.0])
        for i in range(self.n):
            p += self.mass * self.vel[i]
        return p[0]

    '''
    Calculate momentum y dir. Help with testing, not used in game itself.
    '''
    @ti.kernel
    def get_momentum_y(self) -> ti.f32:
        p = ti.Vector([0.0, 0.0])
        for i in range(self.n):
            p += self.mass * self.vel[i]
        return p[1]

'''
Walls for the maxwell's demon game. consist of the 4 boundaries and 2 moveable walls in the middle.
'''
@ti.data_oriented
class Walls(AABBs):
    def __init__(self, elasticity) -> None:
        N, mass = 6, 0
        topleft = ti.Vector.field(2, ti.f32, shape=N)
        bottomright = ti.Vector.field(2, ti.f32, shape=N)
        vel_walls = ti.Vector.field(2, ti.f32, shape=N)
        topleft[0], bottomright[0] = ti.Vector([0, 0]), ti.Vector([0.01, 1])
        topleft[1], bottomright[1] = ti.Vector([0.99, 0]), ti.Vector([1, 1])
        topleft[2], bottomright[2] = ti.Vector([0.01, 0]), ti.Vector([0.99, 0.01])
        topleft[3], bottomright[3] = ti.Vector([0.01, 0.99]), ti.Vector([0.99, 1])
        topleft[4], bottomright[4] = ti.Vector([0.495, 0.01]), ti.Vector([0.505, 0.45])
        topleft[5], bottomright[5] = ti.Vector([0.495, 0.55]), ti.Vector([0.505, 0.99])
        for i in range(N):
            vel_walls[i] = ti.Vector([0, 0]) # all still, no velocity
        super().__init__(N, mass, topleft, bottomright, elasticity, vel_walls)
    
    '''
    center walls move by maxwell's demon, direction either up or down
    '''
    def walls_move(self, up=True, step=0.02):
        if up:
            if self.bottomright[4][1] > step:
                self.bottomright[4][1] -= step
                self.topleft[5][1] -= step
        else:
            if self.topleft[5][1] < 1 - step:
                self.bottomright[4][1] += step
                self.topleft[5][1] += step

'''
Generate a ball's center position within the given range, and a random direction.
'''
def generate_pos_dir(xmin, xmax, ymin, ymax, r):
    pos_x = (xmin + r) + random() * (xmax - xmin - 2 * r)
    pos_y = (ymin + r) + random() * (ymax - ymin - 2 * r)
    theta = random() * 2 * math.pi
    return pos_x, pos_y, theta

'''
Generate center positions and random directions for a given number of balls in the game.
'''
def generate_pos_dir_all(n, r):
    pos_x, pos_y, theta = [None]*n, [None]*n, [None]*n
    for i in range(n):
        sink = True
        while(sink):
            if (random() < 0.5):
                pos_x[i], pos_y[i], theta[i] = generate_pos_dir(0.01, 0.495, 0.01, 0.99, r)
            else:
                pos_x[i], pos_y[i], theta[i] = generate_pos_dir(0.505, 0.99, 0.01, 0.99, r)
            sink = False
            for j in range(i - 1):
                if (pos_x[i] - pos_x[j]) ** 2 + (pos_y[i] - pos_y[j]) ** 2 < r ** 2:
                    sink = True 
    return pos_x, pos_y, theta