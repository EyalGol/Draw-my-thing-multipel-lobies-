import pygame as pg
from pygame.locals import *
from threading import Thread
import socket
from json import dumps, loads
from select import select
from time import sleep

pg.init()


def render_text_center(surface, text, center_cords, color, backround=None):
    font = pg.font.Font(None, 30)
    render = font.render(text, True, color, backround)
    rect = render.get_rect()
    rect.center = center_cords
    surface.blit(render, rect)
    return rect


def render_text_topleft(surface, text, topleft_cords, color, backround=None):
    font = pg.font.Font(None, 30)
    render = font.render(text, True, color, backround)
    rect = render.get_rect()
    rect.topleft = topleft_cords
    surface.blit(render, rect)
    return rect


def render_text_bottomleft(surface, text, bottomleft_cords, color, backround=None):
    font = pg.font.Font(None, 30)
    render = font.render(text, True, color, backround)
    rect = render.get_rect()
    rect.bottomleft = bottomleft_cords
    surface.blit(render, rect)
    return rect


class Game:
    def __init__(self):
        self.is_playing = True
        self.screen = pg.display.set_mode((360, 600))
        self.font = pg.font.Font(None, 30)
        self.client = socket.socket()
        self.chat_log = []
        self.msg = ""
        self.points = []
        self.pid = None
        self.gid = None
        self.last_winner = None
        self.is_drawing = False
        self.answer = ""

    def start_client(self, ip, port, gid=None):
        self.client.connect((ip, int(port)))
        if gid is None:
            data = dumps({"new": True}).encode()
        else:
            data = dumps({"new": False, "gid": gid}).encode()
        self.client.sendall(data)
        json_dump = loads(self.client.recv(1024).decode())
        self.pid = json_dump["pid"]
        self.gid = json_dump["gid"]
        while self.is_playing:
            read, write, _ = select([self.client], [self.client], [])
            if write:
                if self.is_drawing:
                    to_send = dumps({"is_drawing": True, "points": self.points}).encode()
                    self.client.send(to_send)
                else:
                    if len(self.msg) > 0:
                        to_send = dumps({"is_drawing": False, "msg": self.msg}).encode()
                        self.msg = ""
                        self.client.send(to_send)
            if read:
                data = read[0].recv(100000).decode().split("}")[0] + "}"
                print(data)
                data = loads(data)
                if self.pid == data["drawing"]:
                    self.is_drawing = True
                else:
                    self.is_drawing = False
                    self.points = data["points"]
                    self.chat_log = data["chat_log"]
                    self.last_winner = data["last_won"]
                    self.answer = data["answer"]
            sleep(0.1)
        self.client.close()

    def start_menu(self):
        self.screen = pg.display.set_mode((360, 350))
        center = self.screen.get_rect().center
        self.screen.fill((0, 0, 0))
        create_rect = render_text_center(self.screen, "Create a new game", (center[0], center[1] - 50), (255, 255, 255),
                                         (80, 80, 80))
        connect_rect = render_text_center(self.screen, "Connect to an existing game", (center[0], center[1] + 50),
                                          (255, 255, 255), (80, 80, 80))
        pg.display.flip()
        while self.is_playing:
            for evt in pg.event.get():
                if evt.type == QUIT:
                    self.is_playing = False
            is_pressed = pg.mouse.get_pressed()[0]
            if is_pressed:
                pos = pg.mouse.get_pos()
                if create_rect.collidepoint(pos):
                    self.create_menu()
                elif connect_rect.collidepoint(pos):
                    self.connect_menu()

    def connect_menu(self):
        self.screen = pg.display.set_mode((640, 480))
        is_typing = True
        ip = "IP"
        port = "PORT"
        gid = "Game ID"
        editing = None
        while is_typing and self.is_playing:
            for evt in pg.event.get():
                if evt.type == KEYDOWN:
                    if evt.key == K_BACKSPACE:
                        if editing == 0:
                            ip = ip[:-1]
                        elif editing == 1:
                            port += port[:-1]
                        elif editing == 2:
                            gid = gid[:-1]
                    elif editing == 0:
                        ip += evt.unicode
                    elif editing == 1:
                        port += evt.unicode
                    elif editing == 2:
                        gid += evt.unicode
                if evt.type == QUIT:
                    self.is_playing = False
            self.screen.fill((0, 0, 0))
            center = self.screen.get_rect().center
            ip_rect = render_text_center(self.screen, ip, (center[0], center[1] - 70), (255, 255, 255), (80, 80, 80))
            port_rect = render_text_center(self.screen, port, (center[0], center[1] - 25), (255, 255, 255), (80, 80, 80))
            gid_rect = render_text_center(self.screen, gid, (center[0], center[1] + 25), (255, 255, 255), (80, 80, 80))
            connect_button_rect = render_text_center(self.screen, "Connect", (center[0], center[1] + 75), (255, 255, 255),
                                                     (80, 80, 80))
            pg.display.flip()
            is_pressed = pg.mouse.get_pressed()[0]
            if is_pressed:
                pos = pg.mouse.get_pos()
                if ip_rect.collidepoint(pos):
                    ip = ""
                    editing = 0
                elif port_rect.collidepoint(pos):
                    port = ""
                    editing = 1
                elif gid_rect.collidepoint(pos):
                    gid = ""
                    editing = 2
                elif connect_button_rect.collidepoint(pos):
                    Thread(target=self.start_client, args=(ip, port, gid)).start()
                    self.game_start()

    def create_menu(self):
        self.screen = pg.display.set_mode((640, 480))
        is_typing = True
        ip = "IP"
        port = "PORT"
        editing = None
        while is_typing and self.is_playing:
            for evt in pg.event.get():
                if evt.type == KEYDOWN:
                    if evt.key == K_BACKSPACE:
                        if editing == 0:
                            ip = ip[:-1]
                        elif editing == 1:
                            port = port[:-1]
                    elif editing == 0:
                        ip += evt.unicode
                    elif editing == 1:
                        port += evt.unicode
                if evt.type == QUIT:
                    self.is_playing = False
            self.screen.fill((0, 0, 0))
            center = self.screen.get_rect().center
            ip_rect = render_text_center(self.screen, ip, (center[0], center[1] - 50), (255, 255, 255), (80, 80, 80))
            port_rect = render_text_center(self.screen, port, center, (255, 255, 255), (80, 80, 80))
            connect_button_rect = render_text_center(self.screen, "Create", (center[0], center[1] + 50), (255, 255, 255),
                                                     (80, 80, 80))
            pg.display.flip()
            is_pressed = pg.mouse.get_pressed()[0]
            if is_pressed:
                pos = pg.mouse.get_pos()
                if ip_rect.collidepoint(pos):
                    ip = ""
                    editing = 0
                elif port_rect.collidepoint(pos):
                    port = ""
                    editing = 1
                elif connect_button_rect.collidepoint(pos):
                    Thread(target=self.start_client, args=(ip, port)).start()
                    self.game_start()

    def game_start(self):
        width, height = 1000, 500
        msg_current = ""
        self.screen = pg.display.set_mode((width, height))
        while self.is_playing:
            if self.is_drawing:
                for evt in pg.event.get():
                    if evt.type == QUIT:
                        self.is_playing = False
                is_pressed = pg.mouse.get_pressed()[0]
                if is_pressed:
                    pos = pg.mouse.get_pos()
                    if pos[0] < width-413:
                        self.points.append(pos)
            else:
                for evt in pg.event.get():
                    if evt.type == QUIT:
                        self.is_playing = False
                    if evt.type == KEYDOWN:
                        if evt.key == K_RETURN:
                            self.msg = msg_current
                            msg_current = ""
                        elif evt.key == K_BACKSPACE:
                            msg_current = msg_current[:-1]
                        else:
                            msg_current += evt.unicode
            self.screen.fill((230, 230, 230))
            hr = pg.Rect(width-400, 0, 10, height)
            pg.draw.rect(self.screen, (30, 0, 0), hr)
            if self.points:
                for point in self.points:
                    pg.draw.circle(self.screen, (20, 100, 50), point, 15)
            chat_height = 30
            if len(msg_current) > 0:
                render_text_bottomleft(self.screen, msg_current, ((width - 380), (height - chat_height)), (0, 0, 0))
                chat_height += 20
            if self.chat_log:
                for msg in self.chat_log[-1]:
                    render_text_bottomleft(self.screen, msg, ((width - 380), (height - chat_height)), (0, 0, 0))
                    chat_height += 20
            render_text_topleft(self.screen, "PID: " + str(self.pid) + ", GID: " + str(self.gid), (10, 10), (0, 0, 0))
            render_text_topleft(self.screen, "Last winner: " + str(self.last_winner), (10, 30), (0, 0, 0))
            pg.display.flip()


if __name__ == "__main__":
    game = Game()
    game.start_menu()
    pg.quit()