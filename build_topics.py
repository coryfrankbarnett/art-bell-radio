"""Builds topics.json: searchable topic tags for each night, keyed by air date.

The tags are facts only (subjects, people, places and organisations mentioned),
pulled from the show notes of The Art Bell Archive podcast feed. No sentences or
wording from those notes are stored. Run by the weekly GitHub Action.
"""
import html, json, re, time, urllib.request
import xml.etree.ElementTree as ET

APPLE_ID = "1737303645"   # The Art Bell Archive podcast
UA = {"User-Agent": "art-bell-tapes-topic-builder (github.com/coryfrankbarnett/art-bell-radio)"}
MAX_TAGS = 24

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}

# Subjects worth tagging, matched as whole words. key: pattern (lowercase), value: label shown in the app
SUBJECTS = {
    "bigfoot": "Bigfoot", "sasquatch": "Bigfoot", "yeti": "Yeti", "skunk ape": "Skunk Ape", "cryptozoolog": "Cryptozoology",
    "chupacabra": "Chupacabra", "mothman": "Mothman", "loch ness": "Loch Ness", "dogman": "Dogman", "thunderbird": "Thunderbird",
    "ufo": "UFOs", "flying saucer": "UFOs", "flying triangle": "Black triangles", "black triangle": "Black triangles",
    "alien abduction": "Abductions", "abduct": "Abductions", "roswell": "Roswell", "area 51": "Area 51", "majestic": "MJ-12",
    "mj-12": "MJ-12", "crop circle": "Crop circles", "cattle mutilation": "Animal mutilations", "animal mutilation": "Animal mutilations",
    "human mutilation": "Human mutilations", "phoenix lights": "Phoenix Lights", "hale-bopp": "Hale-Bopp", "disclosure": "Disclosure",
    "reptilian": "Reptilians", "grays": "Greys", "greys": "Greys", "men in black": "Men in Black", "star child": "Starchild skull",
    "ghost": "Ghosts", "haunt": "Hauntings", "poltergeist": "Poltergeists", "evp": "EVP", "electronic voice": "EVP",
    "shadow people": "Shadow people", "demon": "Demons", "possession": "Possession", "exorcis": "Exorcism", "angels": "Angels",
    "near-death": "Near-death experiences", "near death": "Near-death experiences", "out-of-body": "Out-of-body experiences",
    "out of body": "Out-of-body experiences", "reincarnation": "Reincarnation", "past life": "Past lives", "past lives": "Past lives",
    "afterlife": "Afterlife", "psychic": "Psychics", "remote view": "Remote viewing", "telepathy": "Telepathy",
    "lucid dream": "Lucid dreaming", "astral": "Astral projection", "time travel": "Time travel",
    "time traveler": "Time travel", "time slip": "Time slips", "parallel universe": "Parallel universes", 
    "prophec": "Prophecy", "prediction": "Predictions", "nostradamus": "Nostradamus", "astrology": "Astrology", "doomsday": "Doomsday",
    "apocalypse": "Apocalypse", "end times": "End times", "y2k": "Y2K", "earth change": "Earth changes", "pole shift": "Pole shift",
    "earthquake": "Earthquakes", "volcano": "Volcanoes", "tsunami": "Tsunamis", "hurricane": "Hurricanes", "weather": "Weather",
    "global warming": "Climate", "climate": "Climate", "superstorm": "Superstorm", "ice age": "Ice ages", "solar flare": "Solar activity",
    "sunspot": "Solar activity", "asteroid": "Asteroids", "comet": "Comets", "planet x": "Planet X", "nibiru": "Planet X",
    "mars": "Mars", "cydonia": "Mars", "face on mars": "Mars", "moon": "The Moon", "apollo": "Apollo", "nasa": "NASA", "seti": "SETI",
    "space station": "Space", "hoagland": "Hoagland", "hollow earth": "Hollow Earth", "atlantis": "Atlantis", "lemuria": "Lemuria",
    "pyramid": "Pyramids", "sphinx": "Sphinx", "egypt": "Egypt", "maya": "Maya", "ancient astronaut": "Ancient astronauts",
    "anunnaki": "Anunnaki", "sumer": "Sumer", "stonehenge": "Stonehenge", "crystal skull": "Crystal skulls", "giants": "Giants",
    "mel's hole": "Mel's Hole", "bottomless hole": "Mel's Hole", "conspirac": "Conspiracies", "illuminati": "Illuminati",
    "new world order": "New World Order", "secret societ": "Secret societies", "freemason": "Freemasons", "jfk": "JFK",
    "kennedy assassination": "JFK", "waco": "Waco", "oklahoma city": "Oklahoma City", "twa 800": "TWA 800", "flight 800": "TWA 800",
    "9/11": "9/11", "september 11": "9/11", "terroris": "Terrorism", "anthrax": "Anthrax", "chemtrail": "Chemtrails",
    "haarp": "HAARP", "mind control": "Mind control", "mk-ultra": "MK-Ultra", "mkultra": "MK-Ultra", "philadelphia experiment": "Philadelphia Experiment",
    "montauk": "Montauk", "tesla": "Tesla", "free energy": "Free energy", "zero point": "Zero-point energy", "anti-gravity": "Anti-gravity",
    "antigravity": "Anti-gravity", "cold fusion": "Cold fusion", "nanotech": "Nanotechnology", "artificial intelligence": "AI",
    "robot": "Robots", "cloning": "Cloning", "genetic": "Genetics", "virus": "Viruses", "pandemic": "Pandemics", "vaccine": "Vaccines",
    "ebola": "Ebola", "bird flu": "Bird flu", "plague": "Plagues", "nuclear": "Nuclear", "survival": "Survival", "economy": "Economy",
    "economic": "Economy", "stock market": "Economy", "internet": "Internet", "privacy": "Privacy",
    "surveillance": "Surveillance", "ham radio": "Ham radio", "shortwave": "Shortwave", "numbers station": "Numbers stations",
    "pirate radio": "Pirate radio", "vampire": "Vampires", "werewolf": "Werewolves", "witch": "Witchcraft", "occult": "Occult",
    "voodoo": "Voodoo", "satan": "Satanism", "bible": "The Bible", "vatican": "Vatican", "fatima": "Fatima", "miracle": "Miracles",
    "stigmata": "Stigmata", "shroud of turin": "Shroud of Turin", "jesus": "Jesus", "rapture": "Rapture", "spontaneous human combustion": "Spontaneous combustion",
    "ball lightning": "Ball lightning", "sea monster": "Sea monsters", "dinosaur": "Dinosaurs", "bermuda triangle": "Bermuda Triangle",
    "skinwalker": "Skinwalkers", "kecksburg": "Kecksburg", "rendlesham": "Rendlesham", "open lines": "Open Lines",
    "ghost to ghost": "Ghost to Ghost", "halloween": "Halloween", "wild card": "Wild Card line", "area 51 caller": "Area 51 caller",
    "remote viewing": "Remote viewing", "orbs": "Orbs", "black helicopter": "Black helicopters", "underground base": "Underground bases",
    "dulce": "Dulce", "hybrid": "Hybrids", "implant": "Implants", "contactee": "Contactees",
}
SUBJECT_RES = [(re.compile(r"(?<![a-z])" + re.escape(k) + r"(?:s|es|ed|ing|ings|ers?|y|ies|ist|ists|ism|ical)?(?![a-z])"), v)
               for k, v in sorted(SUBJECTS.items(), key=lambda kv: -len(kv[0]))]

# In transcripts, these count after one mention; everything else needs a few, so passing remarks don't tag a night
RARE = {"Bigfoot", "Yeti", "Skunk Ape", "Cryptozoology", "Chupacabra", "Mothman", "Loch Ness", "Dogman", "Thunderbird",
        "Mel's Hole", "Skinwalkers", "Kecksburg", "Rendlesham", "Dulce", "Philadelphia Experiment", "Montauk", "Starchild skull",
        "Crystal skulls", "Shadow people", "Phoenix Lights", "Hale-Bopp", "Black triangles", "Men in Black", "Spontaneous combustion",
        "Ball lightning", "Numbers stations", "Bermuda Triangle", "MJ-12", "Planet X", "Hollow Earth", "Atlantis", "Lemuria"}
SKIP_IN_TRANSCRIPT = {"Open Lines", "Ghost to Ghost", "Wild Card line", "Weather", "Internet", "Economy", "Nuclear", "The Moon",
                      "Predictions", "Survival", "Virus", "Robots", "Jesus", "The Bible"}
PODCAST_NS = "https://podcastindex.org/namespace/1.0"
TX_PER_RUN = 1800
TX_DELAY = 0.25


def _unused_transcript_subjects(text):
    low = text.lower()
    found = []
    for rx, label in SUBJECT_RES:
        if label in SKIP_IN_TRANSCRIPT or label in found:
            continue
        n = len(rx.findall(low))
        if n >= (1 if label in RARE else 3):
            found.append(label)
    return found


# Words that start sentences or aren't names; dropped from the front/back of a capitalised run
EDGE = set("""the a an in on at of and or but for to from with without by as after before during while when where
he she they it his her their its this that these those then there here also however meanwhile tonight later next finally first now soon eventually earlier both another other according callers caller art bell art's
dr dr. mr mr. mrs ms professor prof major maj captain col colonel father reverend rev sir""".split())
NOT_NAMES = set(list(MONTHS) + ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                                "coast", "am", "dreamland", "show", "full", "notes", "episode", "hour", "caller", "callers",
                                "listener", "listeners", "american", "god", "lord"])
NAME_RUN = re.compile(r"\b(?:[A-Z]\.|[A-Z][\w'’-]*)(?:\s+(?:(?:de|van|von|der|del|la|le|St\.)(?=\s)|[A-Z]\.|[A-Z][\w'’-]*)){1,5}")


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        return r.read()


def feed_url():
    j = json.loads(get(f"https://itunes.apple.com/lookup?id={APPLE_ID}&entity=podcast"))
    for r in j.get("results", []):
        if r.get("feedUrl"):
            return r["feedUrl"]
    raise SystemExit("Couldn't find the podcast feed")


def plain(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def air_date(title):
    m = re.match(r"\s*([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})", title or "")
    if not m or m.group(1).lower() not in MONTHS:
        return None
    return f"{m.group(3)}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"


def names_in(text):
    out = []
    for m in NAME_RUN.finditer(text):
        words = m.group(0).split()
        while words and words[0].lower().strip(".,") in EDGE:
            words.pop(0)
        while words and words[-1].lower().strip(".,") in EDGE:
            words.pop()
        if len(words) < 2 or len(words) > 5:
            continue
        low = [w.lower().strip(".,'’") for w in words]
        if any(w in NOT_NAMES for w in low) or " ".join(low[:2]) == "art bell":
            continue
        out.append(" ".join(words).strip(".,;:'’"))
    return out


def tags_for(title, notes):
    text = title.split(":", 1)[-1] + " . " + notes
    low = text.lower()
    tags = []
    for rx, label in SUBJECT_RES:
        if rx.search(low):
            tags.append(label)
    tags += names_in(text)
    seen, clean = set(), []
    for t in tags:
        k = t.lower()
        if k not in seen:
            seen.add(k)
            clean.append(t)
    return clean[:MAX_TAGS]


TIME_RX = re.compile(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?")


def to_secs(m):
    h, mi, se = int(m.group(1) or 0), int(m.group(2)), int(m.group(3))
    return h * 3600 + mi * 60 + se


def cues(raw):
    """Split a transcript into (start seconds, text) pieces. Handles WebVTT, SRT, JSON and timestamped text."""
    raw = raw.lstrip("﻿")
    try:
        j = json.loads(raw)
        segs = j.get("segments") if isinstance(j, dict) else j
        out = []
        for sg in segs or []:
            t = sg.get("startTime", sg.get("start"))
            if t is None:
                continue
            out.append((float(t), str(sg.get("body", sg.get("text", "")))))
        if out:
            return out
    except Exception:
        pass
    out = []
    if "-->" in raw:
        for block in re.split(r"\n\s*\n", raw.replace("\r", "")):
            lines = block.strip().split("\n")
            for i, ln in enumerate(lines):
                if "-->" in ln:
                    m = TIME_RX.search(ln)
                    if m:
                        out.append((to_secs(m), " ".join(lines[i + 1:])))
                    break
        if out:
            return out
    parts = re.split(r"[\[(]?((?:\d{1,2}:)?\d{1,2}:\d{2})[\])]?", raw)
    if len(parts) > 3:
        for i in range(1, len(parts) - 1, 2):
            m = TIME_RX.fullmatch(parts[i])
            if m:
                out.append((to_secs(m), parts[i + 1]))
    return out or [(0, raw)]


def scan_transcript(raw):
    """Subject words that come up, and the times they come up. Nothing of the wording is kept."""
    pieces = [(t, re.sub(r"<[^>]+>", " ", txt).lower()) for t, txt in cues(raw)]
    timed = len(pieces) > 1
    subjects, moments = [], {}
    for rx, label in SUBJECT_RES:
        if label in SKIP_IN_TRANSCRIPT:
            continue
        hits = [t for t, txt in pieces for _ in rx.findall(txt)]
        if len(hits) < (1 if label in RARE else 3):
            continue
        if label not in subjects:
            subjects.append(label)
        if timed:
            times = moments.setdefault(label, [])
            for t in sorted(set(int(h) for h in hits)):
                if not times or t - times[-1] > 90:
                    times.append(t)
            moments[label] = times[:12]
    return {"s": subjects, "m": moments}


def dur_secs(s):
    if not s:
        return 0
    if s.isdigit():
        return int(s)
    p = [int(x) for x in s.split(":") if x.isdigit()]
    return sum(v * 60 ** i for i, v in enumerate(reversed(p)))


def main():
    url = feed_url()
    print("feed:", url)
    root = ET.fromstring(get(url))
    ns = {"content": "http://purl.org/rss/1.0/modules/content/", "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
    try:   # the builder's own record of transcripts already scanned (not loaded by the app)
        tx_done = json.load(open("topics-cache.json"))
    except Exception:
        tx_done = {}
    about, mentioned, moments, fetched, failed, kinds = {}, {}, {}, 0, 0, {}

    def add(store, d, tags):
        merged = store.setdefault(d, [])
        have = {x.lower() for x in merged}
        for t in tags:
            if t.lower() not in have:
                merged.append(t); have.add(t.lower())

    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        d = air_date(title)
        if not d:
            continue
        notes = max((plain(it.findtext(p, namespaces=ns)) for p in ("content:encoded", "description", "itunes:summary")), key=len)
        add(about, d, tags_for(title, notes))
        add(about, d, [plain(p.text) for p in it.findall(f"{{{PODCAST_NS}}}person") if plain(p.text) and plain(p.text).lower() != "art bell"])
        key = d + "|" + title
        done = tx_done.get(key)
        if not isinstance(done, dict) and fetched < TX_PER_RUN:
            tx = it.find(f"{{{PODCAST_NS}}}transcript")
            if tx is not None and tx.get("url"):
                try:
                    raw = get(tx.get("url")).decode("utf-8", "replace")
                    kinds[tx.get("type", "?")] = kinds.get(tx.get("type", "?"), 0) + 1
                    done = tx_done[key] = scan_transcript(raw)
                    fetched += 1
                    time.sleep(TX_DELAY)
                except Exception as e:
                    failed += 1
        if isinstance(done, dict):
            have = {x.lower() for x in about.get(d, [])}
            add(mentioned, d, [x for x in done["s"] if x.lower() not in have])
            if done.get("m"):
                moments.setdefault(d, []).append({"len": dur_secs((it.findtext("itunes:duration", namespaces=ns) or "").strip()), "m": done["m"]})
    for d in about:
        about[d] = about[d][:MAX_TAGS + 6]
    if len(about) < 200:
        raise SystemExit(f"Only {len(about)} dated episodes found; keeping the previous topics.json")
    with open("topics.json", "w") as fh:
        json.dump({"built": int(time.time() * 1000), "source": "The Art Bell Archive podcast (facts only: subjects, people, places)",
                   "dates": about, "mentioned": mentioned}, fh, separators=(",", ":"), ensure_ascii=False)
    with open("moments.json", "w") as fh:
        json.dump({"built": int(time.time() * 1000), "dates": moments}, fh, separators=(",", ":"), ensure_ascii=False)
    with open("topics-cache.json", "w") as fh:
        json.dump(tx_done, fh, separators=(",", ":"), ensure_ascii=False)
    print("transcript types:", kinds)
    print("wrote topics.json for", len(about), "dates;", len(moments), "with moments;", fetched, "transcripts scanned this run,", failed, "failed")


if __name__ == "__main__":
    main()
