"""Checks the Telegram bot + public channel setup WITHOUT posting anything.   python -m src.check_bot"""
import requests
from . import config


def call(method, **params):
    r = requests.get(f"https://api.telegram.org/bot{config.TG_BOT_TOKEN}/{method}", params=params, timeout=20)
    return r.json()


def main():
    if not config.TG_BOT_TOKEN:
        raise SystemExit("TG_BOT_TOKEN is empty in .env")
    if not config.PUBLIC_CHANNEL:
        raise SystemExit("PUBLIC_CHANNEL is empty in .env (use @username or the numeric id like -100123...)")
    me = call("getMe")
    if not me.get("ok"):
        raise SystemExit(f"Bot token rejected by Telegram: {me.get('description')}")
    bot = me["result"]
    print(f"✅ Bot OK: @{bot['username']} ({bot['first_name']})")
    chat = call("getChat", chat_id=config.PUBLIC_CHANNEL)
    if not chat.get("ok"):
        raise SystemExit(f"❌ Can't see channel '{config.PUBLIC_CHANNEL}': {chat.get('description')}\n"
                         "   -> add the bot as an ADMIN of the channel, and check the id/@username.")
    c = chat["result"]
    print(f"✅ Channel found: {c.get('title')} (type: {c.get('type')}, id: {c.get('id')})")
    mem = call("getChatMember", chat_id=config.PUBLIC_CHANNEL, user_id=bot["id"])
    if not mem.get("ok"):
        raise SystemExit(f"❌ Can't read the bot's role: {mem.get('description')}")
    m = mem["result"]
    if m["status"] not in ("administrator", "creator"):
        raise SystemExit(f"❌ Bot is '{m['status']}', not admin. Make it an administrator with 'Post messages' permission.")
    can_post = m.get("can_post_messages", True)
    print(f"{'✅' if can_post else '❌'} Bot is admin; can post messages: {can_post}")
    if not can_post:
        raise SystemExit("   -> enable 'Post Messages' for the bot in the channel's admin settings.")
    print("\nAll good. Nothing was posted. (Posting stays off while DRY_RUN=1.)")


if __name__ == "__main__":
    main()
