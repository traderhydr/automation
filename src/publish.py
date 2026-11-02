import requests
from . import config


def telegram_photo(path, caption):
    """Photo + caption. Telegram caps photo captions at 1024 chars; a longer text is sent as a message right after
    the photo (never truncated, so links and disclaimers always survive)."""
    base = f"https://api.telegram.org/bot{config.TG_BOT_TOKEN}"
    short = caption if len(caption) <= 1024 else caption.split("\n\n")[0][:1000]
    with open(path, "rb") as f:
        requests.post(f"{base}/sendPhoto", data={"chat_id": config.PUBLIC_CHANNEL, "caption": short,
                      "parse_mode": "HTML"}, files={"photo": f}).raise_for_status()
    if short is not caption:
        requests.post(f"{base}/sendMessage", data={"chat_id": config.PUBLIC_CHANNEL, "text": caption[:4096], "parse_mode": "HTML",
                      "disable_web_page_preview": True}).raise_for_status()


def telegram_post(paths, caption):
    base = f"https://api.telegram.org/bot{config.TG_BOT_TOKEN}"
    # Telegram caption limit is 1024 chars: send the album, then the full text.
    if len(paths) == 1:
        with open(paths[0], "rb") as f:
            requests.post(f"{base}/sendPhoto", data={"chat_id": config.PUBLIC_CHANNEL},
                          files={"photo": f}).raise_for_status()
    else:
        import json
        media, files = [], {}
        for i, p in enumerate(paths[:10]):
            files[f"f{i}"] = open(p, "rb")
            media.append({"type": "photo", "media": f"attach://f{i}"})
        requests.post(f"{base}/sendMediaGroup", data={"chat_id": config.PUBLIC_CHANNEL,
                      "media": json.dumps(media)}, files=files).raise_for_status()
    requests.post(f"{base}/sendMessage", data={"chat_id": config.PUBLIC_CHANNEL, "text": caption,
                  "parse_mode": "HTML", "disable_web_page_preview": True}).raise_for_status()


def discord_post(paths, text):
    if not config.DISCORD_WEBHOOK_URL:
        return
    from . import links
    text = f"{text}\n\n{links.plain_block()}".strip()
    with open(paths[0], "rb") as f:
        requests.post(config.DISCORD_WEBHOOK_URL, data={"content": text[:1900]},
                      files={"file": f}).raise_for_status()


def x_post(paths, text, tags=""):
    """Post to X with up to 4 images. Needs X API keys (user-context OAuth 1.0a, read+write).
    Note: X's free API tier may not allow media upload; if so the post falls back to text-only."""
    import os
    keys = [os.getenv(k) for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")]
    if not all(keys):
        print("X: keys not set, skipping."); return
    import tweepy
    body = text.strip()
    if tags and len(body) + 1 + len(tags) <= 280:
        body = f"{body}\n{tags}"
    body = body[:280]
    client = tweepy.Client(consumer_key=keys[0], consumer_secret=keys[1],
                           access_token=keys[2], access_token_secret=keys[3])
    try:
        api = tweepy.API(tweepy.OAuth1UserHandler(*keys))
        media = [api.media_upload(p).media_id for p in paths[:4]]
        first = client.create_tweet(text=body, media_ids=media)
        _x_links_reply(client, first)
    except tweepy.errors.Forbidden as e:
        print("X media upload not permitted on this API tier, posting text only:", e)
        first = client.create_tweet(text=body)
        _x_links_reply(client, first)


def _x_links_reply(client, first):
    """Links go in a reply under the post (keeps the main post clean). Plain text, <= 280 chars."""
    from . import links
    txt = links.plain_block()
    if txt:
        client.create_tweet(text=txt[:280], in_reply_to_tweet_id=first.data["id"])


def preview_to_me(paths, text):
    """Send images + caption to YOUR OWN Telegram 'Saved Messages' using the logged-in user session (no bot needed).
    Lets you look at charts on your phone before anything is posted publicly."""
    import asyncio
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    async def go():
        async with TelegramClient(StringSession(config.TG_SESSION_STRING), config.TG_API_ID, config.TG_API_HASH) as c:
            await c.send_file("me", paths[:10], force_document=False)
            await c.send_message("me", text[:4096], parse_mode="html", link_preview=False)
    asyncio.run(go())
    print("Preview sent to your Telegram Saved Messages.")
