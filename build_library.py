"""Builds library.json: the list of Art Bell shows on archive.org.

Run by the GitHub Action in .github/workflows/build-library.yml so the app can
load one small file from its own site instead of querying archive.org on launch.
"""
import json, time, urllib.parse, urllib.request

SOURCES = [
    "the-ultimate-art-bell-collection_202201",
    "ArtBellArea2000",
    "Art-Bell_Midnight_In_the_Desert",
    "ArtBell_Somewhere_In_Time",
    "coast-to-coast-am-with-art-bell-ghost-to-ghost",
    "coast-to-coast-am-w-art-bell-open-lines-collection",
    # extra collections that fill gaps; only dated files, and only Art's own shows
    "art-bell-episodes",
    "art-bell-archive",
    "art-bell-1990-2000",
    "art-bell-2001-to-2010",
]
import re
FULL_DATE = re.compile(r"(19|20)\d\d[-_.]\d\d[-_.]\d\d")
ART_ONLY = {"art-bell-2001-to-2010"}   # mixed collection: keep files that name Art (or his own programmes)
EXTRA = {"art-bell-episodes", "art-bell-archive", "art-bell-1990-2000", "art-bell-2001-to-2010"}


def keep(ident, name):
    if ident not in EXTRA:
        return True
    base = name.split("/")[-1]
    if not FULL_DATE.search(base):
        return False
    if ident in ART_ONLY and not re.search(r"art.?bell|dark.?matter|midnight in the desert|mitd|dreamland", base, re.I):
        return False
    return True
DISCOVER_QUERY = ('mediatype:audio AND (title:("ultimate art bell collection") OR title:("art bell somewhere in time") '
                  'OR title:("art bell dreamland") OR title:("art bell area 2000"))')
UA = {"User-Agent": "art-bell-radio-library-builder (github.com/coryfrankbarnett/art-bell-radio)"}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def discover():
    q = urllib.parse.quote(DISCOVER_QUERY)
    try:
        j = get_json(f"https://archive.org/advancedsearch.php?q={q}&fl[]=identifier&rows=40&output=json")
        return [d["identifier"] for d in j.get("response", {}).get("docs", [])]
    except Exception as e:
        print("discover failed:", e)
        return []


def main():
    ids = list(dict.fromkeys(SOURCES + discover()))
    items = []
    for ident in ids:
        try:
            j = get_json(f"https://archive.org/metadata/{urllib.parse.quote(ident)}")
        except Exception as e:
            print("skip", ident, e)
            continue
        title = j.get("metadata", {}).get("title", ident)
        if isinstance(title, list):
            title = title[0]
        files = [
            {k: f[k] for k in ("name", "size", "length", "source") if k in f}
            for f in j.get("files", [])
            if f.get("name", "").lower().endswith(".mp3") and keep(ident, f.get("name", ""))
        ]
        if files:
            items.append({"id": ident, "title": title, "server": j.get("server"), "dir": j.get("dir"), "files": files})
            print(f"{ident}: {len(files)} mp3s")
        time.sleep(1)
    if not items:
        raise SystemExit("No items fetched; keeping the previous library.json")
    with open("library.json", "w") as fh:
        json.dump({"built": int(time.time() * 1000), "items": items}, fh, separators=(",", ":"))
    print("wrote library.json with", sum(len(i["files"]) for i in items), "files")


if __name__ == "__main__":
    main()
