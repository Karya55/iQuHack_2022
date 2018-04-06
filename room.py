"""
This module is central in Ice Emblem's engine since it provides the Room class
and some functions that uniformly act upon Room objects.
"""


import pygame
import pygame.locals as p
import collections
import logging

import events
import display
import utils


class Room(object):
    """
    Room class is at the heart of Ice Emblem's engine.
    It provides a tree like data structure that can be run in a uniform way by the
    run_room function and allow to route events to registered callbacks or methods
    named like handle_videoresize.
    """
    def __init__(self, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.fps = kwargs.get('fps', display.fps)
        self.wait = kwargs.get('wait', True)
        self.allowed_events = kwargs.get('allowed_events', [])
        self.children = kwargs.get('children', [])
        self.parent = None
        self.done = False
        self.root = False
        self.callbacks = {}

    def prepare_child(self, child):
        child.parent = self
        for grandchild in child.children:
            child.prepare_child(grandchild)

    def add_children(self, *children):
        for child in children:
            self.prepare_child(child)
        self.children.extend(children)

    def add_child(self, child):
        self.add_children(child)

    def remove_child(self, child):
        self.children.remove(child)
        child.parent = None

    def begin_children(self):
        for child in self.children:
            child.begin()

    def begin(self):
        self.begin_children()
        self.logger.debug("begin")

    def loop(self, _events, dt):
        for child in self.children:
            child.loop(_events, dt)
        return self.done

    def draw_children(self, surface=display.window):
        for child in self.children:
            child.draw(surface)

    def draw(self, surface=display.window):
        self.draw_children(surface)

    def end_children(self):
        for child in self.children:
            child.end()

    def end(self):
        self.logger.debug("end")
        self.end_children()

    def handle_videoresize(self, event):
        display.handle_videoresize(event)

    def handle_quit(self, event):
        utils.return_to_os()

    def process_events(self, _events):
        """
        Dispatches an event to registered callbacks or to methods named
        like handle_mousebuttondown.
        """
        for event in _events:
            if event.type in self.callbacks:
                for callback in self.callbacks[event.type]:
                    callback(event)
            method = getattr(self, 'handle_' + pygame.event.event_name(event.type).lower(), None)
            if method is not None:
                method(event)
        for child in self.children:
            child.process_events(_events)

    def register(self, event_type, callback):
        """
        Bind a callback function to an event type.
        """
        if event_type in self.callbacks:
            if callback not in self.callbacks[event_type]:
                self.callbacks[event_type].append(callback)
        else:
            self.callbacks[event_type] = [callback]
        self.logger.debug('registered %s -> %s', pygame.event.event_name(event_type), callback)

    def unregister(self, event_type, callback=None):
        """
        Unregister the latest or the specified callback function from event_type.
        """
        if callback:
            if callback in self.callbacks[event_type]:
                self.callbacks[event_type].remove(callback)
        elif len(self.callbacks[event_type]) > 0:
            self.callbacks[event_type].pop()
        self.logger.debug('unregistered %s -> %s',  pygame.event.event_name(event_type), callback)

    def bind_keys(self, keys, callback):
        """
        Binds a keyboard key to a callback function.
        """
        def f(event):
            for key in keys:
                if event.key == key:
                    callback(self)
        self.register(p.KEYDOWN, f)

    def bind_click(self, mouse_buttons, callback, area=None, inside=True):
        """
        Binds a mouse button to a callback functions.
        The call to the callback can be filtered by area (pygame.Rect) and specify if
        the event position must be inside or outside that area.
        """
        def f(event):
            for mouse_button in mouse_buttons:
                if event.button == mouse_button:
                    if area is None:
                        callback(self)
                    else:
                        collide = area.collidepoint(event.pos)
                        if inside and collide:
                            callback(self)
                        elif not inside and not collide:
                            callback(self)
        self.register(p.MOUSEBUTTONDOWN, f)

    def wait_event(self, timeout=-1):
        _events = events.wait(timeout)
        self.process_events(_events)

    def run_room(self, room):
        run_room(room)
        if self.allowed_events:  # restore allowed events
            events.set_allowed(self.allowed_events)


rooms = collections.deque()
quit = False

def queue_room(room):
    rooms.append(room)

def run_next_room(dequeue=True):
    global quit
    if dequeue:
        run_room(rooms.popleft())
    else:
        run_room(rooms[0])
    quit = False

def run_room(room):
    global quit
    quit = False
    if room.allowed_events:
        events.set_allowed(room.allowed_events)
    room.root = True
    room.begin()
    room.draw()
    display.flip()
    dt = display.tick(room.fps)
    def loop(_events):
        nonlocal dt
        room.process_events(_events)
        done = room.loop(_events, dt) or quit
        if not done:
            room.draw()
            display.draw_fps()
            display.flip()
            dt = display.tick(room.fps)
        return done
    events.event_loop(loop, room.wait)
    if not quit:
        room.end()
    room.root = False

def run():
    global quit
    quit = False
    while rooms:
        run_next_room()

def stop():
    global rooms, quit
    rooms = collections.deque()
    quit = True