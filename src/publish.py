import requests
from . import config


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
        client.create_tweet(text=body, media_ids=media)
    except tweepy.errors.Forbidden as e:
        print("X media upload not permitted on this API tier, posting text only:", e)
        client.create_tweet(text=body)
