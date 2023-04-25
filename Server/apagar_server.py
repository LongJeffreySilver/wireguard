

import subprocess
import time

server_name = "wg0"
subprocess.Popen(["systemctl", "stop", "wg-quick@" + server_name + ".service"])
#subprocess.Popen(["wg-quick", "down", "wg-quick@" + server_name])
time.sleep(5)
#subprocess.Popen(["rm", "-r", "private_key.key", "public_key.key.pub", "wg0.conf", "__pycache__"]) #stdin="private_key.key public_key.key.pub wg0.conf __pycache__"