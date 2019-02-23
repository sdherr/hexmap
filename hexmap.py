#!/usr/bin/python
"""
A simple interactive HexMap. My kids like playing with this as a game in itself, but the real
intention is that you can use this as a basis for whatever else you are making. Requires Pygame.

Controls are mouse-based.
Left-click creates a new hex or changes the color of one.
Left-drag rotates the map.
Right-drag pans the map.
Scroll-wheel zooms.
Scroll-wheel-click resets zoom and re-centeres the map.

Credit for "the hard parts" in this file goes to Amit at Red Blob Games:
https://www.redblobgames.com/grids/hexagons/
"""

import sys
import pygame
import random
import math
import collections

Point = collections.namedtuple("Point", ["x", "y"])
Orientation = collections.namedtuple("Orientation", ["f0", "f1", "f2", "f3", "b0", "b1", "b2", "b3", "start_angle"])
Layout = collections.namedtuple("Layout", ["orientation", "size", "origin"])

layout_pointy = Orientation(math.sqrt(3.0), math.sqrt(3.0) / 2.0, 0.0, 3.0 / 2.0, math.sqrt(3.0) / 3.0, -1.0 / 3.0, 0.0, 2.0 / 3.0, 0.5)
layout_flat = Orientation(3.0 / 2.0, 0.0, math.sqrt(3.0) / 2.0, math.sqrt(3.0), 2.0 / 3.0, 0.0, -1.0 / 3.0, math.sqrt(3.0) / 3.0, 0.0)
PI_OVER_THREE = math.pi / 3.0


class Position(tuple):
    # Using Cube/Axial coordinates
    def __new__(cls, q, r, s=None):
        if s == None:
            s = -1 * q - r
        return tuple.__new__(Position, (q, r, s))

    @property
    def q(self):
        return self[0]

    @property
    def r(self):
        return self[1]

    @property
    def s(self):
        return self[2]

    def round(self):
        """Convert fractional coordinates into the actual position of the containing hex."""
        qi = int(round(self.q))
        ri = int(round(self.r))
        si = int(round(self.s))
        q_diff = abs(qi - self.q)
        r_diff = abs(ri - self.r)
        s_diff = abs(si - self.s)
        if q_diff > r_diff and q_diff > s_diff:
            qi = -ri - si
        else:
            if r_diff > s_diff:
                ri = -qi - si
            else:
                si = -qi - ri
        return Position(qi, ri, si)


class HexMap:
    ONE_THIRD = 1. / 3
    TWO_THIRDS = 2. / 3
    SQRT_3_OVER_3 = 3**0.5 / 3
    STARTING_HEX_SIZE = Point(100.0, 100.0)

    def __init__(self, size):
        self.size = size
        self.map_surface = pygame.Surface(size)
        self.layout = Layout(layout_pointy, self.STARTING_HEX_SIZE, Point(size[0] / 2, size[1] / 2))
        self.hexes = {}
        origin = Position(0, 0)
        self.hexes[origin] = Hex(self.map_surface, origin, self.layout)

    def click(self, location):
        pos = self.pixel_to_hex(Point(location[0], location[1]))
        if pos in self.hexes:
            self.hexes[pos].click()
        else:
            hex = Hex(self.map_surface, pos, self.layout)
            self.hexes[pos] = hex

    def _recalculate_hex_corners(self):
        for hex in self.hexes.values():
            hex.recalculate_corners(self.layout)

    def zoom(self, change):
        size = Point(self.layout.size[0] * change, self.layout.size[1] * change)
        self.layout = Layout(self.layout.orientation, size, self.layout.origin)
        self._recalculate_hex_corners()

    def reset(self, size):
        self.layout = Layout(self.layout.orientation, self.STARTING_HEX_SIZE, Point(size[0] / 2, size[1] / 2))
        self._recalculate_hex_corners()

    def pan(self, x_travel, y_travel):
        self.layout = Layout(self.layout.orientation, self.layout.size, Point(self.layout.origin[0] + x_travel,
                                                                              self.layout.origin[1] + y_travel))
        self._recalculate_hex_corners()

    def rotate_right(self):
        if self.layout.orientation == layout_pointy:
            self.layout = Layout(layout_flat, self.layout.size, self.layout.origin)
            new_hexes = {}
            for position in self.hexes:
                x, y, z = position
                new_position = Position(-z, -x, -y)
                hex = self.hexes[position]
                hex.position = new_position
                new_hexes[new_position] = hex
            self.hexes = new_hexes
        else:
            self.layout = Layout(layout_pointy, self.layout.size, self.layout.origin)
        self._recalculate_hex_corners()

    def rotate_left(self):
        if self.layout.orientation == layout_flat:
            self.layout = Layout(layout_pointy, self.layout.size, self.layout.origin)
            new_hexes = {}
            for position in self.hexes:
                x, y, z = position
                new_position = Position(-y, -z, -x)
                hex = self.hexes[position]
                hex.position = new_position
                new_hexes[new_position] = hex
            self.hexes = new_hexes
        else:
            self.layout = Layout(layout_flat, self.layout.size, self.layout.origin)
        self._recalculate_hex_corners()

    def pixel_to_hex(self, p):
        M = self.layout.orientation
        size = self.layout.size
        origin = self.layout.origin
        pt = Point((p.x - origin.x) / size.x, (p.y - origin.y) / size.y)
        q = M.b0 * pt.x + M.b1 * pt.y
        r = M.b2 * pt.x + M.b3 * pt.y
        return Position(q, r).round()

    def draw(self, screen):
        self.map_surface.fill((0, 0, 0))  # black
        for hex in self.hexes.values():
            hex.draw()
        screen.blit(self.map_surface, (0,0))


class Hex:
    DIRECTIONS = [(1, 0, -1), (1, -1, 0), (0, -1, 1), (-1, 0, 1), (-1, 1, 0), (0, 1, -1)]

    def __init__(self, map, position, layout):
        self.position = position
        self.map = map

        # Calculate the points that define the vertexes.
        self.points = self.corners(layout, position)
        self.color = self.random_color()

    @staticmethod
    def random_color():
        return (random.randint(0,255), random.randint(0,255), random.randint(0,255))

    def recalculate_corners(self, layout):
        self.points = self.corners(layout, self.position)

    @staticmethod
    def hex_to_pixel(layout, h):
        M = layout.orientation
        size = layout.size
        origin = layout.origin
        x = (M.f0 * h.q + M.f1 * h.r) * size.x
        y = (M.f2 * h.q + M.f3 * h.r) * size.y
        return Point(x + origin.x, y + origin.y)

    @staticmethod
    def corner_offset(layout, corner):
        M = layout.orientation
        size = layout.size
        angle = PI_OVER_THREE * (M.start_angle - corner)
        return Point(size.x * math.cos(angle), size.y * math.sin(angle))

    @staticmethod
    def corners(layout, h):
        corners = []
        center = Hex.hex_to_pixel(layout, h)
        for i in range(0, 6):
            offset = Hex.corner_offset(layout, i)
            corners.append(Point(center.x + offset.x, center.y + offset.y))
        return corners

    def neighbors(self):
        neighbors = []
        for direction in self.DIRECTIONS:
            neighbors.append(Position(self.position[0] + direction[0],
                                      self.position[1] + direction[1],
                                      self.position[2] + direction[2]))
        return neighbors

    def click(self):
        self.color = self.random_color()

    def draw(self):
        pygame.draw.polygon(self.map, self.color, self.points, 1)


if __name__ == '__main__':
    pygame.init()

    size = width, height = 1200, 1000
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(size)

    LEFT_BUTTON, MIDDLE_BUTTON, RIGHT_BUTTON, SCROLL_UP, SCROLL_DOWN = 1, 2, 3, 4, 5

    hex_map = HexMap(size)
    mouse_drag_orig_angle = None
    mouse_drag_orig_pos = None
    was_moved = False

    while True:
        # max the busy-wait loop at 60 FPS
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == SCROLL_DOWN:
                    hex_map.zoom(.95)
                elif event.button == SCROLL_UP:
                    hex_map.zoom(1.05)
                elif event.button == LEFT_BUTTON:
                    if not was_moved:
                        hex_map.click(event.pos)
                    mouse_drag_orig_angle = None
                    was_moved = False
                elif event.button == RIGHT_BUTTON:
                    mouse_drag_orig_pos = None
                elif event.button == MIDDLE_BUTTON:
                    hex_map.reset(size)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == LEFT_BUTTON:
                    mouse_drag_orig_angle = math.atan2(event.pos[1] - hex_map.layout.origin.y, event.pos[0] - hex_map.layout.origin.x)
                elif event.button == RIGHT_BUTTON:
                    mouse_drag_orig_pos = event.pos

            elif event.type == pygame.MOUSEMOTION:
                if mouse_drag_orig_angle:  # if we're rotating it
                    new_angle = math.atan2(event.pos[1] - hex_map.layout.origin.y, event.pos[0] - hex_map.layout.origin.x)
                    difference = math.degrees(mouse_drag_orig_angle - new_angle)
                    if difference > 180: 
                        difference -= 360
                    elif difference < -180:
                        difference += 360
                    if abs(difference) > 30:
                        if difference > 0:
                            hex_map.rotate_right()
                        else:
                            hex_map.rotate_left()
                        mouse_drag_orig_angle = new_angle
                        was_moved = True
                elif mouse_drag_orig_pos:  # if we're dragging it
                    hex_map.pan(event.pos[0] - mouse_drag_orig_pos[0], event.pos[1] - mouse_drag_orig_pos[1])
                    mouse_drag_orig_pos = event.pos

        screen.fill((0, 0, 0))  # black
        hex_map.draw(screen)
        pygame.display.flip()