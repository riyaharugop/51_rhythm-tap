import pygame
import random

LANES = 4

# D, F, J, K are the four lane keys
LANE_KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]

LANE_LABELS = ['D', 'F', 'J', 'K']

LANE_COLORS = [
    (220, 80, 80),
    (80, 180, 220),
    (100, 220, 100),
    (220, 180, 60)
]


class Note:

    WIDTH = 70

    # Normal tap note height
    HEIGHT = 20

    # Hold note height
    HOLD_HEIGHT = 80

    def __init__(self, lane, y=-30, speed=4, is_hold=False):

        self.lane = lane
        self.y = y
        self.speed = speed

        # True if this is a hold note
        self.is_hold = is_hold

        # Used by the game engine
        self.hit = False
        self.missed = False

        # Used only for hold notes
        self.holding = False
        self.hold_time = 0

    def update(self):
        self.y += self.speed

    def get_rect(self, lane_x):

        # Hold notes are visually longer
        if self.is_hold:
            height = self.HOLD_HEIGHT
        else:
            height = self.HEIGHT

        return pygame.Rect(
            lane_x - self.WIDTH // 2,
            int(self.y),
            self.WIDTH,
            height
        )