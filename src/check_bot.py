"""Checks the Telegram bot + public channel setup WITHOUT posting anything.   python -m src.check_bot"""
import requests
from . import config


def call(method, **params):
    r = requests.get(f"https://api.telegram.org/bot{config.TG_BOT_TOKEN}/{method}", params=params, timeout=20)
    return r.json()


def main():
    if not config.TG_BOT_TOKEN:
        raise SystemExit("TG_BOT_TOKEN is empty in .env")
    chans = config.ALL_POST_CHANNELS
    if not chans:
        raise SystemExit("PUBLIC_CHANNEL is empty in .env (comma separate several: @a,-1001234567890)")
    me = call("getMe")
    if not me.get("ok"):
        raise SystemExit(f"Bot token rejected by Telegram: {me.get('description')}")
    bot = me["result"]
    print(f"✅ Bot OK: @{bot['username']} ({bot['first_name']})")
    bad = 0
    for ch in chans:
        chat = call("getChat", chat_id=ch)
        if not chat.get("ok"):
            print(f"❌ {ch}: can't see it ({chat.get('description')}) -> add the bot as ADMIN and check the id"); bad += 1; continue
        c = chat["result"]
        mem = call("getChatMember", chat_id=ch, user_id=bot["id"])
        m = mem.get("result", {}) if mem.get("ok") else {}
        ok = m.get("status") in ("administrator", "creator") and m.get("can_post_messages", True)
        print(f"{'✅' if ok else '❌'} {c.get('title')} ({c.get('type')}, id {c.get('id')}): bot is {m.get('status', 'unknown')}"
              + ("" if ok else " -> make it admin with 'Post Messages'"))
        bad += 0 if ok else 1
    routing = {"Reports": config.CHANNELS_REPORTS, "Free signals": config.CHANNELS_SIGNALS, "BTC outlook": config.CHANNELS_OUTLOOK}
    print("\nRouting:", "; ".join(f"{k} -> {', '.join(v)}" for k, v in routing.items()))
    if bad:
        raise SystemExit(f"\n{bad} channel(s) need fixing. Nothing was posted.")
    print("\nAll good. Nothing was posted. (Posting stays off while DRY_RUN=1.)")


if __name__ == "__main__":
    main()
