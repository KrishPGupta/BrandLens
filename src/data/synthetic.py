"""Synthetic brand-post generator so the full pipeline runs without downloads.
Schema matches what real data must provide (see loader.REQUIRED)."""
import numpy as np
import pandas as pd

POS_W = ["love", "amazing", "great", "fantastic", "excellent", "smooth", "reliable", "impressed", "brilliant", "best", "superb"]
NEG_W = ["hate", "terrible", "awful", "broken", "worst", "disappointed", "useless", "scam", "laggy", "garbage", "annoying"]
NEU_W = ["announced", "released", "update", "available", "launching", "spotted", "scheduled", "listed", "rumor", "version"]
POOL = {"positive": POS_W, "negative": NEG_W, "neutral": NEU_W}
TEMPLATES = [
    "{b} is {w} honestly",
    "just tried {b} and it feels {w}",
    "{b} support was {w} today",
    "my {b} order arrived and it is {w}",
    "thoughts on {b}: {w}",
]
HANDLES = ["techguy", "daily_deals", "sarah_k", "mikeR", "newsdesk", "gadgetfan"]
BOT_TEMPLATES = [
    "Check out {b}!!! best deal ever {u} #ad #win #{bl}",
    "WIN a free {b} now {u} #giveaway @{h} @{h2}",
    "{b} is amazing buy now {u} #sale #{bl} #promo",
]


def _url(rng):
    return "http://bit.ly/" + "".join(rng.choice(list("abcdefghijklmnop"), 6))


def _human_text(rng, brand, label):
    cls = label if rng.random() > 0.12 else str(rng.choice(list(POOL)))
    w = str(rng.choice(POOL[cls]))
    t = str(rng.choice(TEMPLATES)).format(b=brand, w=w)
    if rng.random() < 0.35:
        t += f" #{brand.lower()}"
    if rng.random() < 0.25:
        t = f"@{rng.choice(HANDLES)} " + t
    if rng.random() < 0.15:
        t += " http://t.co/" + "".join(rng.choice(list("abcdefghij"), 6))
    return t


def _bot_text(rng, brand):
    return str(rng.choice(BOT_TEMPLATES)).format(
        b=brand, bl=brand.lower(), u=_url(rng),
        h=rng.choice(HANDLES), h2=rng.choice(HANDLES))


def _make_accounts(rng, n_h, n_b):
    humans, bots = [], []
    for i in range(n_h):
        age = int(rng.integers(200, 4000))
        humans.append(dict(user_id=f"h{i}", is_bot=0,
                           followers=int(rng.lognormal(5.5, 1.3)),
                           following=int(rng.lognormal(5.2, 0.9)),
                           account_age_days=age,
                           statuses_count=int(age * rng.uniform(0.2, 6))))
    for i in range(n_b):
        if rng.random() < 0.12:   # stealthy bots look human -> classifier is not perfect
            age = int(rng.integers(150, 3000))
            f, g, spd = rng.lognormal(5, 1.2), rng.lognormal(5.5, 1.0), rng.uniform(0.5, 8)
        else:
            age = int(rng.integers(5, 400))
            f, g, spd = rng.lognormal(2.5, 1.0), rng.lognormal(6.5, 0.8), rng.uniform(20, 120)
        bots.append(dict(user_id=f"b{i}", is_bot=1, followers=int(f), following=int(g),
                         account_age_days=age, statuses_count=int(age * spd)))
    return humans, bots


def generate(n_weeks=26, posts_per_brand_week=250, brands=("Nova", "Pulse", "Zenith"),
             seed=42, start="2025-01-06", drift_brand="Nova", drift_week=15):
    rng = np.random.default_rng(seed)
    humans, bots = _make_accounts(rng, 1500, 250)
    t0 = pd.Timestamp(start)
    rows, pid = [], 0
    for w in range(n_weeks):
        for b in brands:
            drifting = (b == drift_brand and w >= drift_week)
            p = [0.25, 0.20, 0.55] if drifting else [0.50, 0.20, 0.30]   # pos, neu, neg
            bot_share = 0.30 if drifting else 0.10
            for _ in range(posts_per_brand_week):
                ts = t0 + pd.Timedelta(weeks=w) + pd.Timedelta(seconds=int(rng.integers(0, 7 * 86400)))
                if rng.random() < bot_share:
                    a = bots[int(rng.integers(len(bots)))]
                    text, label = _bot_text(rng, b), "positive"
                else:
                    a = humans[int(rng.integers(len(humans)))]
                    label = str(rng.choice(["positive", "neutral", "negative"], p=p))
                    text = _human_text(rng, b, label)
                rows.append({"post_id": pid, "brand": b, "text": text, "timestamp": ts,
                             "label": label, **a})
                pid += 1
    return pd.DataFrame(rows)
