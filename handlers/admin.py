@router.message(Command("loop"))
async def cmd_loop(m: Message, bot: Bot):
    parts = (m.text or "").split()
    arg = parts[1].lower() if len(parts) > 1 else "status"
    if arg == "start":
        region = parts[2].upper() if len(parts) > 2 else None
        ok = await loop.start(bot, region)
        await m.answer("▶️ Loop chalu." if ok else "⚠️ Pehle se chal raha hai.")
    elif arg == "stop":
        ok = await loop.stop()
        await m.answer("⏹ Loop band." if ok else "⚠️ Loop chal hi nahi raha.")
    else:
        await m.answer(f"<b>Loop:</b> {loop.status()}\n\nUse: <code>/loop start [REGION]</code> | <code>/loop stop</code>")


@router.message(Command("genstats"))
async def cmd_genstats(m: Message):
    total = await db.count_accounts()
    await m.answer(f"📊 Total accounts: <b>{total}</b>\nLoop: {loop.status()}\n\nClear: /cleardb")


@router.message(Command("cleardb"))
async def cmd_cleardb(m: Message):
    n = await db.count_accounts()
    await db.clear_accounts()
    await m.answer(f"🗑 {n} accounts delete ho gaye.")