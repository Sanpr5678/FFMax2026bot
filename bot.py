from config import LOOP_AUTOSTART
    if LOOP_AUTOSTART:
        import loop
        await loop.start(bot)
