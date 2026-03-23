
import sys
import time
sys.path.append("/Users/juliandiazlombardoemery/Desktop/Minecraft/My Minecraft AI Project/src")
print(sys.path)

from core.bot_client import MinecraftBot
from tools.movement.movement import move_forward_or_backwards, move_left_or_right

def test_movement():
    """
    Test the movement functions.
    """
    bot = MinecraftBot()
    print("wating for the bot to spawn...") # <== this prints dont work how they should
    time.sleep(5)
    print("bot has spawned, moving forward and backward...") # <== this prints dont work how they should
    for i in range(10):
        move_forward_or_backwards(bot, 20, True)
        time.sleep(1)
        move_forward_or_backwards(bot, 20, False)
        time.sleep(1)
    print("moving left and right...")
    for i in range(10):
        move_left_or_right(bot, 20, True)
        time.sleep(1)
        move_left_or_right(bot, 20, False)
        time.sleep(1)


test_movement()