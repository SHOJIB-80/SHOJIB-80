"""
cards.py — generates stats/lang/activity SVGs into assets/
Run:  python scripts/cards.py
Env:  GITHUB_TOKEN  (optional but gives higher rate limits)
      GITHUB_USER   (defaults to SHOJIB-80)
"""

import os, json, math, textwrap, datetime, urllib.request, urllib.parse

# ── config ────────────────────────────────────────────────────────────────────
USER    = os.environ.get("GITHUB_USER", "SHOJIB-80")
TOKEN   = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUT_DIR, exist_ok=True)

ACCENT      = "#58A6FF"
DARK_BG     = "#0D1117"
DARK_BORDER = "#30363D"
DARK_TEXT   = "#C9D1D9"
DARK_MUTED  = "#8B949E"
LIGHT_BG     = "#FFFFFF"
LIGHT_BORDER = "#D0D7DE"
LIGHT_TEXT   = "#1F2328"
LIGHT_MUTED  = "#656D76"

# ── GitHub helpers ─────────────────────────────────────────────────────────────
def gh(path):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        "User-Agent": "readme-cards/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  API error {path}: {e}")
        return None


def get_stats():
    u = gh(f"/users/{USER}") or {}
    repos = gh(f"/users/{USER}/repos?per_page=100&type=owner") or []

    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)

    langs: dict[str, int] = {}
    for r in repos:
        if r.get("fork"):
            continue
        name = r["name"]
        data = gh(f"/repos/{USER}/{name}/languages") or {}
        for lang, bytes_ in data.items():
            langs[lang] = langs.get(lang, 0) + bytes_

    return {
        "public_repos":  u.get("public_repos", len(repos)),
        "followers":     u.get("followers", 0),
        "stars":         stars,
        "forks":         forks,
        "langs":         langs,
    }


# ── SVG primitives ─────────────────────────────────────────────────────────────
def svg_open(w, h, bg, border):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">\n'
        f'<rect width="{w}" height="{h}" rx="10" ry="10" '
        f'fill="{bg}" stroke="{border}" stroke-width="1"/>\n'
    )

def svg_text(x, y, text, fill, size=13, weight="normal", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="Segoe UI,system-ui,sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}">{text}</text>\n'
    )

def svg_rect(x, y, w, h, fill, rx=4):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>\n'


# ── stats card ─────────────────────────────────────────────────────────────────
def make_stats_svg(stats, dark: bool) -> str:
    bg, border, text, muted = (
        (DARK_BG, DARK_BORDER, DARK_TEXT, DARK_MUTED) if dark
        else (LIGHT_BG, LIGHT_BORDER, LIGHT_TEXT, LIGHT_MUTED)
    )
    W, H = 400, 170
    tiles = [
        ("Repos",     stats["public_repos"]),
        ("Stars",     stats["stars"]),
        ("Forks",     stats["forks"]),
        ("Followers", stats["followers"]),
    ]
    out = svg_open(W, H, bg, border)
    out += svg_text(20, 32, "GitHub Stats", text, size=15, weight="600")
    out += svg_text(20, 52, f"@{USER}", muted, size=11)

    tw = (W - 40) // len(tiles)
    for i, (label, val) in enumerate(tiles):
        x = 20 + i * tw
        out += svg_text(x + tw//2, 100, str(val), ACCENT, size=22, weight="700", anchor="middle")
        out += svg_text(x + tw//2, 118, label, muted, size=11, anchor="middle")

    out += svg_text(W - 14, H - 12, f"Updated {datetime.date.today()}", muted, size=9, anchor="end")
    out += "</svg>"
    return out


# ── language bar card ──────────────────────────────────────────────────────────
def make_langs_svg(langs: dict, dark: bool) -> str:
    bg, border, text, muted = (
        (DARK_BG, DARK_BORDER, DARK_TEXT, DARK_MUTED) if dark
        else (LIGHT_BG, LIGHT_BORDER, LIGHT_TEXT, LIGHT_MUTED)
    )

    # filter & sort
    EXCLUDE = {"html", "css", "shell", "makefile", "dockerfile", "batchfile"}
    filtered = {k: v for k, v in langs.items() if k.lower() not in EXCLUDE}
    total = sum(filtered.values()) or 1
    top = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:6]

    LANG_COLORS = {
        "PHP": "#4F5D95", "JavaScript": "#F1E05A", "Python": "#3572A5",
        "Java": "#B07219", "TypeScript": "#3178C6", "C": "#555555",
        "C++": "#F34B7D", "CSS": "#563D7C", "HTML": "#E34C26",
        "Jupyter Notebook": "#DA5B0B",
    }

    W = 400
    H = 60 + len(top) * 28 + 20
    out = svg_open(W, H, bg, border)
    out += svg_text(20, 32, "Top Languages", text, size=15, weight="600")

    BAR_W = W - 40
    # colored progress bar
    x = 20
    out += f'<rect x="{x}" y="44" width="{BAR_W}" height="8" rx="4" fill="{border}"/>\n'
    for lang, val in top:
        color = LANG_COLORS.get(lang, "#8B949E")
        w = int(BAR_W * val / total)
        out += f'<rect x="{x}" y="44" width="{w}" height="8" rx="0" fill="{color}"/>\n'
        x += w

    for i, (lang, val) in enumerate(top):
        color = LANG_COLORS.get(lang, "#8B949E")
        pct   = val / total * 100
        ry    = 60 + i * 28
        out += f'<circle cx="30" cy="{ry + 5}" r="5" fill="{color}"/>\n'
        out += svg_text(42, ry + 10, lang, text, size=12)
        out += svg_text(W - 20, ry + 10, f"{pct:.1f}%", muted, size=11, anchor="end")

    out += "</svg>"
    return out


# ── activity wave card ─────────────────────────────────────────────────────────
def make_activity_svg(dark: bool) -> str:
    """Generates a simple placeholder wave. Replace with real data if desired."""
    bg, border, text, muted = (
        (DARK_BG, DARK_BORDER, DARK_TEXT, DARK_MUTED) if dark
        else (LIGHT_BG, LIGHT_BORDER, LIGHT_TEXT, LIGHT_MUTED)
    )
    W, H = 800, 120
    out = svg_open(W, H, bg, border)
    out += svg_text(20, 32, "Contribution Activity", text, size=15, weight="600")
    out += svg_text(20, 50, "See the full graph on GitHub profile", muted, size=11)

    # decorative wave
    import math
    pts = []
    for i in range(W + 1):
        y = 85 + 18 * math.sin((i / W) * 6 * math.pi) * ((i / W) * (1 - i / W) * 4)
        pts.append(f"{i},{y:.1f}")
    path_d = "M " + " L ".join(pts)
    out += (
        f'<path d="{path_d}" fill="none" stroke="{ACCENT}" '
        f'stroke-width="2" opacity="0.7"/>\n'
    )
    out += svg_text(W - 14, H - 10, f"@{USER} · {datetime.date.today()}", muted, size=9, anchor="end")
    out += "</svg>"
    return out


# ── main ───────────────────────────────────────────────────────────────────────
def write(name, content):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote {name}")


if __name__ == "__main__":
    print(f"Fetching data for {USER}…")
    stats = get_stats()
    print(f"  repos={stats['public_repos']} stars={stats['stars']} forks={stats['forks']}")

    print("Generating stats cards…")
    write("stats-dark.svg",    make_stats_svg(stats, dark=True))
    write("stats-light.svg",   make_stats_svg(stats, dark=False))

    print("Generating language cards…")
    write("langs-dark.svg",    make_langs_svg(stats["langs"], dark=True))
    write("langs-light.svg",   make_langs_svg(stats["langs"], dark=False))

    print("Generating activity cards…")
    write("activity-dark.svg",  make_activity_svg(dark=True))
    write("activity-light.svg", make_activity_svg(dark=False))

    print("Done.")
