from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import db
import ffapi
from config import ADMIN_IDS, CHANNEL_URL, DEFAULT_REGION, SUPPORT_URL

router = Router()

WELCOME = (
    "<b>🔥 FF MAX Bot</b>\n\n"
    "Yahan se latest version, official download links, redeem codes aur player stats mil jayenge.\n\n"
    "Commands:\n"
    "/version — latest version\n"
    "/download — download links\n"
    "/codes — active codes\n"
    "/stats &lt;uid&gt; [region] — player info"
)


class Info(StatesGroup):
    waiting_uid = State()


def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📥 Latest Version", callback_data="m:version")
    kb.button(text="⬇️ Download Links", callback_data="m:download")
    kb.button(text="🎁 Redeem Codes", callback_data="m:codes")
    kb.button(text="🔍 Player Info", callback_data="m:info")
    if is_admin:
        kb.button(text="🛠 Admin Panel", callback_data="a:panel")
    kb.adjust(1)
    return kb.as_markup()


async def _maintenance() -> bool:
    return (await db.get_setting("maintenance", "0")) == "1"


@router.message(CommandStart())
async def start(m: Message):
    await db.upsert_user(m.from_user.id, m.from_user.username)
    if await _maintenance() and m.from_user.id not in ADMIN_IDS:
        await m.answer("🛠 Bot abhi maintenance mode me hai. Thodi der baad try karo.")
        return
    await m.answer(WELCOME, reply_markup=main_menu(m.from_user.id in ADMIN_IDS))


@router.callback_query(F.data == "m:version")
async def cb_version(c: CallbackQuery):
    v = await db.get_setting("version", "OB55")
    note = await db.get_setting("note", "")
    text = f"<b>📦 Latest live version:</b> {v}"
    if note:
        text += f"\n\n📝 {note}"
    text += "\n\nDownload links ke liye /download dabao."
    await c.message.edit_text(text, reply_markup=main_menu(c.from_user.id in ADMIN_IDS))
    await c.answer()


@router.callback_query(F.data == "m:download")
async def cb_download(c: CallbackQuery):
    v = await db.get_setting("version", "OB55")
    rows = await db.list_apks(v)
    if not rows:
        await c.answer("Abhi koi link add nahi hua.", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    for _id, _ver, label, url in rows:
        kb.button(text=f"⬇️ {label}", url=url)
    kb.button(text="🔙 Back", callback_data="m:home")
    kb.adjust(1)
    await c.message.edit_text(
        f"<b>⬇️ FF MAX {v} Download Links</b>\n\nSirf official / trusted source se download karo.",
        reply_markup=kb.as_markup(),
    )
    await c.answer()


@router.callback_query(F.data == "m:codes")
async def cb_codes(c: CallbackQuery):
    rows = await db.list_codes()
    if not rows:
        await c.message.edit_text(
            "🎁 Abhi koi active code nahi hai. Baad me check karo.",
            reply_markup=main_menu(c.from_user.id in ADMIN_IDS),
        )
        await c.answer()
        return
    lines = [f"<code>{code}</code> — {reward or 'Reward'}" for _id, code, reward in rows]
    await c.message.edit_text(
        "<b>🎁 Redeem Codes</b>\n\n" + "\n".join(lines) + "\n\n<i>Code FF MAX → Profile → Redeem me daalo.</i>",
        reply_markup=main_menu(c.from_user.id in ADMIN_IDS),
    )
    await c.answer()


@router.callback_query(F.data == "m:home")
async def cb_home(c: CallbackQuery):
    await c.message.edit_text(WELCOME, reply_markup=main_menu(c.from_user.id in ADMIN_IDS))
    await c.answer()


@router.callback_query(F.data == "m:info")
async def cb_info(c: CallbackQuery, state: FSMContext):
    await state.set_state(Info.waiting_uid)
    await c.message.edit_text(
        f"🔍 Player ka <b>UID</b> bhejo.\n\nRegion default: <b>{DEFAULT_REGION}</b>\n"
        "Alag region chahiye to: <code>UID REGION</code> (e.g. <code>123456789 PK</code>)"
    )
    await c.answer()


@router.message(Info.waiting_uid)
async def got_uid(m: Message, state: FSMContext):
    await state.clear()
    parts = (m.text or "").split()
    if not parts or not parts[0].isdigit():
        await m.answer("❌ Sahi UID bhejo (sirf numbers).")
        return
    uid = parts[0]
    region = parts[1].upper() if len(parts) > 1 and parts[1].upper() in ffapi.REGIONS else DEFAULT_REGION
    wait = await m.answer("⏳ Stats nikal raha hoon...")
    try:
        data = await ffapi.player_info(uid, region)
        await wait.edit_text(ffapi.format_player(data, uid, region))
    except ffapi.FFError:
        await wait.edit_text("❌ API se data nahi mila. UID/region check karo ya thodi der baad try karo.")


@router.message(Command("version"))
async def cmd_version(m: Message):
    v = await db.get_setting("version", "OB55")
    note = await db.get_setting("note", "")
    await m.answer(f"<b>Latest version:</b> {v}" + (f"\n\n{note}" if note else ""))


@router.message(Command("download"))
async def cmd_download(m: Message):
    v = await db.get_setting("version", "OB55")
    rows = await db.list_apks(v)
    if not rows:
        await m.answer("Koi link available nahi.")
        return
    kb = InlineKeyboardBuilder()
    for _id, _ver, label, url in rows:
        kb.button(text=f"⬇️ {label}", url=url)
    kb.adjust(1)
    await m.answer(f"<b>FF MAX {v} links:</b>", reply_markup=kb.as_markup())


@router.message(Command("codes"))
async def cmd_codes(m: Message):
    rows = await db.list_codes()
    if not rows:
        await m.answer("Abhi koi active code nahi.")
        return
    await m.answer("<b>🎁 Codes:</b>\n\n" + "\n".join(f"<code>{c}</code> — {r or 'Reward'}" for _i, c, r in rows))


@router.message(Command("stats"))
async def cmd_stats(m: Message):
    parts = (m.text or "").split()[1:]
    if not parts or not parts[0].isdigit():
        await m.answer("Use: <code>/stats UID [REGION]</code>")
        return
    uid = parts[0]
    region = parts[1].upper() if len(parts) > 1 and parts[1].upper() in ffapi.REGIONS else DEFAULT_REGION
    wait = await m.answer("⏳ Stats nikal raha hoon...")
    try:
        data = await ffapi.player_info(uid, region)
        await wait.edit_text(ffapi.format_player(data, uid, region))
    except ffapi.FFError:
        await wait.edit_text("❌ Data nahi mila. UID/region check karo.")
        _cooldown: dict[int, float] = {}


@router.message(Command("gen"))
async def cmd_gen(m: Message):
    if await _maintenance() and m.from_user.id not in ADMIN_IDS:
        await m.answer("🛠 Maintenance mode.")
        return
    last = _cooldown.get(m.from_user.id, 0)
    if time.time() - last < GEN_COOLDOWN and m.from_user.id not in ADMIN_IDS:
        await m.answer(f"⏳ Thoda ruko: {int(GEN_COOLDOWN - (time.time() - last))}s baad try karo.")
        return
    parts = (m.text or "").split()
    count = min(int(parts[1]), GEN_MAX_PER_REQ) if len(parts) > 1 and parts[1].isdigit() else 1
    region = parts[2].upper() if len(parts) > 2 else GEN_REGION
    _cooldown[m.from_user.id] = time.time()

    wait = await m.answer(f"⏳ {count} account bana raha hoon ({region})...")
    accs, fails = [], 0
    for _ in range(count):
        try:
            a = await gen.create_account(region)
            await db.add_account(a["uid"], a["password"], a["region"], a.get("jwt"), m.from_user.id)
            accs.append(a)
        except Exception:
            fails += 1
        await asyncio.sleep(0.4)

    if not accs:
        await wait.edit_text("❌ Koi account nahi bana. API/token fail hui, thodi der baad try karo.")
        return

    body = "\n".join(f"{a['uid']}|{a['password']}" for a in accs)
    txt = f"# FF MAX guest accounts ({region})\n# format: uid|password\n{body}\n"
    await wait.edit_text(f"✅ {len(accs)} account bane" + (f" | ❌ {fails} fail" if fails else ""))
    await m.answer_document(
        BufferedInputFile(txt.encode(), filename=f"ffmax_{region}_{len(accs)}.txt"),
        caption="<i>UID|PASS se FF MAX me guest login karo. Turant password change kar lo.</i>",
    )


@router.message(Command("myacc"))
async def cmd_myacc(m: Message):
    rows = await db.recent_accounts(10, m.from_user.id)
    if not rows:
        await m.answer("Tumne abhi tak koi account nahi banaya. /gen se banao.")
        return
    lines = [f"<code>{u}</code> | <code>{p}</code> | {r}" for u, p, r, _t in rows]
    await m.answer("<b>🔑 Tumhare last accounts</b>\n\n" + "\n".join(lines))
