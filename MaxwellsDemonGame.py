"""The main script of the Maxwell's Demon Game.

fixed number of white balls and yellow balls(default 15 each) are randomly generated. The goal for the player is to move
the whole on the wall by pressing UP and DOWN on the keyboard, and get all yellow balls to one
side and all white balls to the other side.

The game ends when the player successfully move all balls to the correct side, or the time counts down to zero.
"""

import taichi as ti
from BallsAndWalls import Balls, Walls
import time
from BallsAndWalls import generate_pos_dir_all

__author__ = "507C"
__credits__ = ["507C", "Y7K4"]
__version__ = "1.0.1"
__maintainer__ = "507C"

if __name__ == "__main__":

    ti.init(arch=ti.cpu)

    # object parameters
    N1, N2, radius = 15, 15, 0.015
    pos_x, pos_y, theta = generate_pos_dir_all(N1 + N2, radius)
    mass, init_speed, elasticity = 1, 80, 1

    # initialize objects: walls and 2 group of balls
    balls1 = Balls(N=N1, mass=mass, pos_x=pos_x[:N1], pos_y=pos_y[:N1], theta=theta[:N1], radius=0.015, init_speed= init_speed, elasticity=elasticity)
    balls2 = Balls(N=N2, mass=mass, pos_x=pos_x[N1:], pos_y=pos_y[N1:], theta=theta[N1:], radius=radius, init_speed=init_speed, elasticity=elasticity)
    walls = Walls(elasticity=elasticity)

    # gui and game parameters
    my_gui = ti.GUI("Game of Maxwell's Demon", (600, 600))
    h = 5e-5 # time-step size
    total_time = 90 # max time for player if not success
    success = False
    time_up = False
    time_start = time.perf_counter()
    
    while my_gui.running:
        # print rules with user-friendly color
        my_gui.text("Yellow balls to the left", pos = (0.1, 0.9), color=0xffd500)
        my_gui.text("White balls to the right", pos = (0.6, 0.9))
        # if success, print message
        if success:
            my_gui.text("Congrats, you win!", pos=(0.5, 0.5), font_size=30)
        # otherwise, update success, deal with time up issue
        else:
            if balls1.detect_success(True) and balls2.detect_success(False):
                success = True            
            # print the scor if time up
            if time_up:
                score = (balls1.success_ball_number(True) + balls2.success_ball_number(False)) / (N1 + N2) * 100
                my_gui.text("Your score: " + str(int(score)), pos=(0.5, 0.5), font_size=30)
                my_gui.text("Game over.", pos=(0.1, 0.85), color=0xff0000)
                my_gui.text("Press Esc to exit.", pos=(0.1, 0.8), color=0xff0000)
            # otherwise, calculate and print the remaining time
            else:
                time_remain = total_time + time_start - time.perf_counter()
                if time_remain <= 0:
                    time_up = True
                my_gui.text("Time remain: " + str(int(time_remain)), pos=(0.1, 0.85), color=0xff0000)
                my_gui.text("Press Esc to stop immediately.", pos=(0.1, 0.8), color=0xff0000)
        
        # uncomment the following block for testing. Ek should not change over time. px and py for the system will be inf for walls has inf mass.
        # my_gui.text("Ek: " + str(int(balls1.get_kinetic_energy() + balls2.get_kinetic_energy())), pos=(0.1, 0.75), color=0xff0000)
        # my_gui.text("px: " + str(int(balls1.get_momentum_x() + balls2.get_momentum_x())), pos=(0.1, 0.7), color=0xff0000)
        # my_gui.text("py: " + str(int(balls1.get_momentum_y() + balls2.get_momentum_y())), pos=(0.1, 0.65), color=0xff0000)

        # user interaction
        for e in my_gui.get_events(ti.GUI.PRESS):
            # XXX: the whole board is upside down, down-> up, up -> down
            if e.key == ti.GUI.UP:
                walls.walls_move(up=False)
            elif e.key == ti.GUI.DOWN:
                walls.walls_move(up=True)
            elif e.key == ti.GUI.ESCAPE:
                if not time_up and not success:
                    time_up = True
                else:
                    exit()

        # display all balls and walls status
        for pair_obj_color in ([balls1, 0xffd500], [balls2, 0xffffff], [walls, 0xffffff]):
            pair_obj_color[0].display(my_gui, color=pair_obj_color[1])

        # update to next step if neither success nor time up 
        if not success and not time_up:
            # compute impulse vs self, walls and other balls respectively
            for pair_ball_other in ([balls1, balls2], [balls2, balls1]):
                pair_ball_other[0].compute_impulse_vs_self()
                pair_ball_other[0].compute_impulse_vs_AABB(walls)
                pair_ball_other[0].compute_impulse_vs_circle(pair_ball_other[1])
            # do the update after all impulse calculation
            for balls in (balls1, balls2):
                balls.update(h)
        
        my_gui.show()