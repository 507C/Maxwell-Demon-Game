"""Provides Rigid2dBodies class and its 2 Subclasses: Circles and AABBs.

Rigid bodies are non-deformable self-defined shapes, with no squashing or stretching allowed.
We provide a class Rigid2dBodies as general rigid bodies, and 2 shapes: Circles and AABB
(Axis Aligned Bounding Boxes) as specific examples.
We care about the collision between rigid bodies. Specifically, Impulse will be calculated and
applied.
Sinking of objects are not dealt with due to time reason.
"""

import taichi as ti
from random import random
from random import seed

__author__ = "507C"
__credits__ = ["507C", "Y7K4"]
__version__ = "1.0.1"
__maintainer__ = "507C"

'''
Rigid bodies. Non-deformable, no squashing or stretching allowed.
'''
@ti.data_oriented
class Rigid2dBodies:
    def __init__(self, N, mass, elasticity, vel_init) -> None:
        # 2d rigid body object-related field
        self.n = N
        self.mass = mass # set mass = 0 for mass = inf
        self.elasticity = elasticity
        self.vel = vel_init
        self.d_vel = ti.Vector.field(2, ti.f32, shape=self.n)
        self.inv_mass = mass # use inv_mass to save cal time in every itr and deal with inf mass case 
        if self.mass == 0:
            self.inv_mass = 0
        else:
            self.inv_mass = 1/self.mass

    def display(self, gui, color=0xffffff):
        pass

    @ti.func
    def clear_d_vel(self):
        for i in self.d_vel:
            self.d_vel[i] = ti.Vector([0.0, 0.0])

    @ti.kernel
    def update(self, h: ti.f32):
        pass

    @staticmethod
    @ti.func
    def get_impulse(rv, normal, elasticity1, elasticity2, inv_mass1, inv_mass2):
        # relative velocity in terms of the normal direction
        vel_along_normal = rv[0] * normal[0] + rv[1] * normal[1]
        # Do not resolve if velocities are separating(impulse = 0)
        impulse = ti.Vector([0.0, 0.0])
        # If not separating, calculate impulse
        if vel_along_normal < 0:
            e = min(elasticity1, elasticity2)
            j = -(1 + e) * vel_along_normal
            j /= inv_mass1 + inv_mass2
            impulse = j * normal
        return impulse

'''
Circles, each circle represented by a center pos and a radius
'''
@ti.data_oriented
class Circles(Rigid2dBodies):
    def __init__(self, N, mass, pos, radius, elasticity, vel_init) -> None:
        super().__init__(N, mass, elasticity, vel_init)
        self.pos = pos # pos of center
        self.radius = radius

    def display(self, gui, pic_size=600, color=0xffffff):
        gui.circles(self.pos.to_numpy(), radius=self.radius * pic_size, color=color)

    '''
    resolve collision between bodies inside Circle object
    '''
    @ti.kernel
    def compute_impulse_vs_self(self):
        for i in range(self.n):
            for j in range(self.n):
                # resolve collision. Update both for time saving.
                if i < j:            
                    diff = self.pos[j] - self.pos[i]
                    if diff.norm() < 2 * self.radius:
                        # relative velocity
                        rv = self.vel[j] - self.vel[i]
                        # normal relative position
                        normal = diff / diff.norm()
                        # get impulse
                        impulse = Rigid2dBodies.get_impulse(rv, normal, self.elasticity, 
                            self.elasticity, self.inv_mass, self.inv_mass)
                        # update both i and j
                        self.d_vel[i] -= self.inv_mass * impulse
                        self.d_vel[j] += self.inv_mass * impulse

    '''
    resolve collision between Circle object and another Circle object
    '''
    @ti.kernel
    def compute_impulse_vs_circle(self, circles: ti.template()):
        for i in range(self.n):
            for j in range(circles.n):
                # resolve collision                    
                diff = circles.pos[j] - self.pos[i]
                if diff.norm() < self.radius + circles.radius:
                    # relative velocity
                    rv = circles.vel[j] - self.vel[i]
                    # normal relative position
                    normal = diff / diff.norm()
                    # get impulse
                    impulse = Rigid2dBodies.get_impulse(rv, normal, self.elasticity, 
                        circles.elasticity, self.inv_mass, circles.inv_mass)
                    # update d_vel[i]
                    self.d_vel[i] -= self.inv_mass * impulse

    '''
    resolve collision between Circle object and AABB object
    '''
    @ti.kernel
    def compute_impulse_vs_AABB(self, aabbs: ti.template()):
        for i in range(self.n):
            for j in range(aabbs.n):
                #calculate normal
                pos_j = (aabbs.topleft[j] + aabbs.bottomright[j])/2
                n = self.pos[i] - pos_j
                closest = n
                x_extent = abs(aabbs.topleft[j][0] - aabbs.bottomright[j][0]) / 2
                y_extent = abs(aabbs.topleft[j][1] - aabbs.bottomright[j][1]) / 2
                closest[0] = max(min(closest[0], x_extent), -x_extent)
                closest[1] = max(min(closest[1], y_extent), -y_extent)
                normal = n - closest
                # resolve collision
                if normal.norm() < self.radius:
                    # relative velocity
                    rv = - aabbs.vel[j] + self.vel[i]
                    # normal relative position
                    normal /= normal.norm()
                    # get impulse
                    impulse = Rigid2dBodies.get_impulse(rv, normal, self.elasticity, 
                        aabbs.elasticity, self.inv_mass, aabbs.inv_mass)
                    # update d_vel[i]
                    self.d_vel[i] += self.inv_mass * impulse
    
    @ti.kernel
    def update(self, h: ti.f32):
        # update vel and pos
        for i in self.vel:            
            self.vel[i] += self.d_vel[i]
            self.pos[i] += h * self.vel[i]
        # clear d_vel for the next itr
        self.clear_d_vel()
    
'''
Axis Aligned Bounding Boxes, each box represent by the topleft point and the bottomright point
'''
@ti.data_oriented
class AABBs(Rigid2dBodies):
    def __init__(self, N, mass, topleft, bottomright, elasticity, vel_init) -> None:
        super().__init__(N, mass, elasticity, vel_init)
        self.topleft = topleft
        self.bottomright = bottomright

    def display(self, gui, color=0xffffff):
        for i in range(self.n):
            gui.rect(self.topleft[i], self.bottomright[i], radius=1, color=color)

    @ti.kernel
    def update(self, h: ti.f32):
        # update vel and pos
        for i in self.vel:
            self.vel[i] += self.d_vel[i]
            self.topleft[i] += h * self.vel[i]
            self.bottomright[i] += h * self.vel[i]
        # clear d_vel for the next itr
        self.clear_d_vel()
