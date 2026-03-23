def move_forward_or_backwards(bot, n_of_ticks: int, for_or_back: bool):
    """
    Move the bot forward or backward.
    
    Args:
        bot: The bot instance.
        for_or_back: True to move forward, False to move backward.
    """
    if for_or_back:
        bot.walk("forward", n_of_ticks = n_of_ticks)
    else:
        bot.walk("back", n_of_ticks = n_of_ticks)
    
def move_left_or_right(bot, n_of_ticks: int, left_or_right: bool):
    """
    Move the bot left or right.
    
    Args:
        bot: The bot instance.
        left_or_right: True to move left, False to move right.
    """
    if left_or_right:
        bot.walk("left", n_of_ticks = n_of_ticks)
    else:
        bot.walk("right", n_of_ticks = n_of_ticks)
