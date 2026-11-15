"""Checks your X (Twitter) keys WITHOUT posting.   python -m src.check_x"""
import os
from . import config  # loads .env

KEYS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")


def main():
    missing = [k for k in KEYS if not os.getenv(k)]
    if missing:
        raise SystemExit(f"❌ Missing in .env: {', '.join(missing)}")
    import tweepy
    client = tweepy.Client(consumer_key=os.environ[KEYS[0]], consumer_secret=os.environ[KEYS[1]],
                           access_token=os.environ[KEYS[2]], access_token_secret=os.environ[KEYS[3]])
    try:
        me = client.get_me()
    except tweepy.errors.Unauthorized:
        raise SystemExit("❌ X rejected the keys (401). Re-copy all four; if you changed app permissions, regenerate the Access Token & Secret.")
    except tweepy.errors.Forbidden as e:
        raise SystemExit(f"❌ X says forbidden (403): {e}\n   Your plan/app may not allow this call; check developer.x.com → your app → permissions/plan.")
    except Exception as e:
        raise SystemExit(f"❌ Could not reach X: {e}")
    print(f"✅ Keys work. Posting as @{me.data.username} (id {me.data.id}).")
    print("   Reminder: the app must have 'Read and Write' permission, or posting will fail with 403.")
    print("   Nothing was posted.")


if __name__ == "__main__":
    main()
