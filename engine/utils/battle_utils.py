

def atk_per_sec(spd_base: float, spd_stat: float):
    """
    Calculate attacks per second given a move speed and a speed stat.

    The current math is that each SPD stat point will reduce the combat ticks required
    to execute a fast move by 5%.

    1000 combat ticks in 1 second.
    """
    return 1000.0 / (spd_base * 1 - (spd_stat * .05))
