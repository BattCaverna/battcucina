#!/usr/bin/env python3

import time
import random
import sys
from rpi_ws281x import *
import RPi.GPIO as GPIO
import threading
import queue
import socketserver
import inspect


class CmdTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # self.request is the TCP socket connected to the client
        while True:
            line = self.request.recv(1024)
            if len(line) == 0:
                return
            data = line.strip().split()
            if len(data) > 0:
                cmd = data[0].decode()
                for command in inspect.getmembers(self, predicate=inspect.ismethod):
                    if command[0] == "cmd_" + cmd:
                        ret = command[1](data)
                        if ret == None:
                            return
                        elif ret[0] == 0:
                            self.request.sendall(("0 Command OK.%s%s\n" % (
                                "\n" if len(ret) > 1 else "", "\n".join(ret[1:]))).encode())
                        elif ret[0] == -2:
                            self.request.sendall(
                                "-2 Invalid arguments.\n".encode())
                        else:
                            self.request.sendall(
                                "%d Error.%s\n" % "\n".join(ret[1:]).encode())
                        break
                else:
                    self.request.sendall("-1 Command not found.\n".encode())
                # self.request.sendall("\n")

    def cmd_setout(self, args):
        try:
            val = int(args[1])
        except:
            return [-2]

        self.server.strip.put(val)
        return [0]

    def cmd_getout(self, args):
        val = self.server.strip.get_state()
        ret = [0]
        ret.append("1" if val else "0")
        return ret


def R(color):
    return (color >> 16) & 0xff


def G(color):
    return (color >> 8) & 0xff


def B(color):
    return color & 0xff


def gen_buffer(start, stop, len):
    strip = []
    dr = (R(stop) - R(start))/float(len)
    dg = (G(stop) - G(start))/float(len)
    db = (B(stop) - B(start))/float(len)
    c = [R(start), G(start), B(start)]
    for i in range(int(len)):
        strip.append(Color(int(c[0]), int(c[1]), int(c[2])))
        c[0] += dr
        c[1] += dg
        c[2] += db
    return strip


# LED strip configuration:
LED_COUNT = 191     # number of LED pixels.
LED_PIN = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT = False   # True to invert the signal (when using NPN transistor)

COLOR_ON = Color(255, 160, 72)  # Color(255, 240, 100)
COLOR_OFF = Color(0, 0, 0)

cmd_queue = queue.Queue()


MSG_OFF = 0
MSG_ON = 1
MSG_TOGGLE = 2
MSG_COLOR_MOVE = 3
MSG_CNT = 4


class LedThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.color = [COLOR_OFF, COLOR_ON]
        self.state = 0
        self.strip = Adafruit_NeoPixel(
            LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
        self.strip.begin()
        self.buf = []
        self.buf = gen_buffer(self.color[1], Color(
            255, 50, 50), self.strip.numPixels()/2)
        self.buf = self.buf + list(reversed(self.buf))
        if self.strip.numPixels() % 2:
            self.buf.append(self.color[1])

        self.transitions = [self.stripStart, self.stripEnd,
                            self.stripMid, self.fade, self.randomic]
        self.lock = threading.RLock()

    def put(self, msg):
        self.queue.put(msg)

    def get_state(self):
        with self.lock:
            return self.state

    def run(self):
        move = True
        while True:
            msg = None
            try:
                msg = self.queue.get(True, 0.5)
            except queue.Empty:
                pass

            with self.lock:
                if msg is not None:
                    on = self.state
                    if msg == MSG_TOGGLE:
                        on = 1 - on
                    elif msg == MSG_COLOR_MOVE:
                        if on == 0:
                            self.state = on = 1
                            for i in range(self.strip.numPixels()):
                                self.strip.setPixelColor(i, self.buf[i])
                        else:
                            on = 0
                    elif msg < MSG_CNT:
                        on = msg
                    if on != self.state:
                        random.choice(self.transitions)(self.color[on])
                    self.state = on

                if move:
                    led = self.strip.getPixels()
                    a = led[0]
                    led = led[1:]
                    led.append(a)
                    for i in range(self.strip.numPixels()):
                        self.strip.setPixelColor(i, led[i])

                self.strip.show()

    def setColor(self, color):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
        self.strip.show()

    def stripColorFrom(self, dir, color):
        start = 0
        inc = +1
        if dir < 0:
            start = self.strip.numPixels() - 1
            inc = -1

        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(start, color)
            start += inc
            if not (i % 5):
                self.strip.show()
        self.strip.show()

    def stripStart(self, color):
        self.stripColorFrom(1, color)

    def stripEnd(self, color):
        self.stripColorFrom(-1, color)

    def stripMid(self, color):
        mid = int(self.strip.numPixels() / 2)
        for i in range(mid):
            self.strip.setPixelColor(mid+i, color)
            self.strip.setPixelColor(mid-i, color)
            if not (i % 3):
                self.strip.show()
        self.strip.setPixelColor(0, color)
        self.strip.setPixelColor(self.strip.numPixels() - 1, color)
        self.strip.show()

    def randomic(self, color):
        idx = list(range(self.strip.numPixels()))
        random.shuffle(idx)
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(idx[i], color)
            if not (i % 5):
                self.strip.show()

    def fade(self, color, wait=0):
        step = 5.0
        delta = []
        leds = self.strip.getPixels()
        for i in range(self.strip.numPixels()):
            r = R(color) - R(leds[i])
            g = G(color) - G(leds[i])
            b = B(color) - B(leds[i])
            delta.append((r/step, g/step, b/step))

        for s in range(int(step)):
            for i in range(self.strip.numPixels()):
                r = int(max(R(leds[i]) + delta[i][0], 0))
                g = int(max(G(leds[i]) + delta[i][1], 0))
                b = int(max(B(leds[i]) + delta[i][2], 0))
                self.strip.setPixelColor(i, Color(r, g, b))
            self.strip.show()
            time.sleep(wait/1000.0)

        self.setColor(color)


prev_press = time.time()

def gpio_callback(arg):
    global prev_press
    now = time.time()

    pb = {17: "induction hob", 27: "coffee"}
    print("Button pressed: %s side" % pb[arg], flush=True)

    if (now - prev_press) < 2:
        cmd_queue.put(MSG_COLOR_MOVE)
    else:
        cmd_queue.put(MSG_TOGGLE)

    prev_press = now


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


# Main program logic follows:
if __name__ == '__main__':
    led = LedThread(cmd_queue)
    led.daemon = True
    led.start()

    GPIO.setmode(GPIO.BCM)
    pb_piano = 27
    pb_caffe = 17
    GPIO.setup(pb_piano, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(pb_caffe, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(pb_piano, GPIO.FALLING, gpio_callback, bouncetime=300)
    GPIO.add_event_detect(pb_caffe, GPIO.FALLING, gpio_callback, bouncetime=300)

    HOST, PORT = "0.0.0.0", 8023

    # Create the server
    server = ThreadedTCPServer((HOST, PORT), CmdTCPHandler)
    server.strip = led

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
