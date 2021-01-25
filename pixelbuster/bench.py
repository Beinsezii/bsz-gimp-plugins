#!/usr/bin/python3

import ctypes
from sys import platform
EXTENSIONS = {"win32": ".dll", "linux": ".so"}
import os.path
pixelbuster = ctypes.CDLL(
    os.path.dirname(os.path.realpath(__file__)) +
    "/../pixelbuster" + EXTENSIONS.get(platform)
).pixelbuster
pixelbuster.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]

import struct
import time
import random

count = (4000 * 3000) * 4  # 4 channels, common hd camera resolution

pixels = struct.pack('d' * count, *[random.random() for _ in range(count)])
size = len(pixels)


# simple test aka 'best case'
code = """
r + 1
r + 1
r + 1
r + 1
r + 1
r - 5
""".encode('UTF-8')
now = time.perf_counter()
pixelbuster(code, "rgba".encode('UTF-8'), pixels, size)
print(time.perf_counter() - now)

# test most ops aka 'worst case'
code = """
v = r
r + pi
r - pi
r * 2
r / 2
r sqrt r
r pow 2
r min 100
r max 0
r abs r
r log e
r round r
r = v
""".encode('UTF-8')
now = time.perf_counter()
pixelbuster(code, "rgba".encode('UTF-8'), pixels, size)
print(time.perf_counter() - now)

# filmic chroma impl aka 'simple real case'
scale = 100
offset = 1.25
code = f"""
v = {offset}
v2 = l
v2 / {scale}
v - v2
c * v
""".encode('UTF-8')
now = time.perf_counter()
pixelbuster(code, "lcha".encode('UTF-8'), pixels, size)
print(time.perf_counter() - now)
