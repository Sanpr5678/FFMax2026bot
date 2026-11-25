import aiohttp

from config import FF_API_BASE

REGIONS = ["IND", "BD", "PK", "SG", "ID", "MY", "TH", "VN", "BR", "US", "ME", "CIS", "RU", "TW"]


class FFError(Exception):
    pass


async def player_info(uid: str, region: str) -> dict:
    url = f"{FF_API_BASE}/playerstats"
    timeout = aiohttp.ClientTimeout(total=30)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(url, params={"uid": uid, "region": region.upper()}) as r:
                if r.status != 200:
                    raise FFError(f"API returned {r.status}")
                return await r.json(content_type=None)
    except aiohttp.ClientError as e:
        raise FFError(str(e)) from e


def _g(d: dict, *keys, default="—"):
    for k in keys:
        v = d.get(k) if isinstance(d, dict) else None
        if v not in (None, "", [], {}):
            return v
    return default


def format_player(d: dict, uid: str, region: str) -> str:
    p = d.get("data") or d.get("player") or d.get("result") or d
    if isinstance(p, list) and p:
        p = p[0]
    if not isinstance(p, dict):
        return f"<b>UID:</b> <code>{uid}</code>\n<b>Region:</b> {region}\n\nRaw:\n<code>{str(d)[:900]}</code>"

    nick = _g(p, "nickname", "name", "player_name")
    level = _g(p, "level", "account_level")
    rank = _g(p, "rank", "br_rank", "rank_name")
    likes = _g(p, "likes", "liked")
    kills = _g(p, "kills", "total_kills")
    wins = _g(p, "wins", "total_wins")
    matches = _g(p, "matches", "games_played", "total_matches")
    created = _g(p, "created_at", "create_time", "account_created")

    return (
        f"<b>👤 {nick}</b>\n"
        f"🆔 <code>{uid}</code> | 🌍 {region}\n"
        f"⭐ Level: {level}\n"
        f"🏆 Rank: {rank}\n"
        f"👍 Likes: {likes}\n"
        f"🎯 Kills: {kills} | 🥇 Wins: {wins} | 🎮 Matches: {matches}\n"
        f"📅 Created: {created}"
    )
