"""
Akdam Social Automation
Generates a caption using Gemini, then posts it to Bluesky and Mastodon.
Runs automatically via GitHub Actions on a schedule.
"""

import os
import sys
import requests

# ---------- Load secrets from environment (set by GitHub Actions) ----------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE")
BLUESKY_PASSWORD = os.environ.get("BLUESKY_PASSWORD")
MASTODON_HANDLE = os.environ.get("MASTODON_HANDLE")
MASTODON_ACCESS_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN")
MASTODON_INSTANCE = "hear-me.social"

# Content pillars Akdam posts about - edit this list anytime to change topics
CONTENT_PILLARS = [
    "a quick Shopify optimization tip for small e-commerce brands",
    "a practical tip for improving Meta/Google ad performance on a small budget",
    "a short insight about email marketing with Klaviyo for e-commerce",
    "a conversion rate optimization (CRO) tip for online stores",
    "an encouraging insight for small business owners about growing online",
]


def generate_caption():
    """Ask Gemini to write a short social media caption."""
    import random
    topic = random.choice(CONTENT_PILLARS)

    prompt = (
        f"Write a short, engaging social media caption (under 250 characters) "
        f"about {topic}. Written for Akdam, a digital marketing agency serving "
        f"e-commerce and local businesses. No hashtags in the first line. "
        f"Sound like a helpful expert, not a salesperson. "
        f"Return ONLY the caption text, nothing else, no quotation marks."
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    caption = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    return caption


def post_to_bluesky(text):
    """Post text to Bluesky using the AT Protocol."""
    try:
        session_resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.server.createSession",
            json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_PASSWORD},
            timeout=30,
        )
        session_resp.raise_for_status()
        session = session_resp.json()

        from datetime import datetime, timezone

        post_resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {session['accessJwt']}"},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": {
                    "text": text,
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                },
            },
            timeout=30,
        )
        post_resp.raise_for_status()
        print("✅ Posted to Bluesky")
        return True
    except Exception as e:
        print(f"❌ Bluesky post failed: {e}")
        return False


def post_to_mastodon(text):
    """Post text to Mastodon using its REST API."""
    try:
        resp = requests.post(
            f"https://{MASTODON_INSTANCE}/api/v1/statuses",
            headers={"Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}"},
            data={"status": text},
            timeout=30,
        )
        resp.raise_for_status()
        print("✅ Posted to Mastodon")
        return True
    except Exception as e:
        print(f"❌ Mastodon post failed: {e}")
        return False


def main():
    print("Generating caption with Gemini...")
    caption = generate_caption()
    print(f"Caption generated:\n{caption}\n")

    bluesky_ok = post_to_bluesky(caption)
    mastodon_ok = post_to_mastodon(caption)

    if not bluesky_ok and not mastodon_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
