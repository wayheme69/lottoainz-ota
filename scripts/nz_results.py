#!/usr/bin/env python3
"""Robot LOTTO AI NZ : résultats officiels Lotto NZ (API publique mylotto.co.nz — pathway.mylotto.co.nz).
- 30 derniers tirages : 6 numéros + Bonus Ball, Powerball, Strike (ordre de tirage), gains et gagnants de chaque division
- prochain tirage (date, jackpots annoncés) si l'API le fournit
Écrit nz_results.json UNIQUEMENT si tout est cohérent ; ajoute les tirages nouveaux à history.json (sans réécrire l'existant)."""
import json, urllib.request, datetime, time, os, sys
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
H = {"User-Agent": UA, "Accept": "application/json", "Origin": "https://mylotto.co.nz", "Referer": "https://mylotto.co.nz/"}
B = "https://pathway.mylotto.co.nz/api"

def get(path, tries=4):
    for t in range(tries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, headers=H), timeout=60).read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            if t == tries - 1: raise
        except Exception:
            if t == tries - 1: raise
        time.sleep(4 * (t + 1))

def money(v):
    try: return float(v)
    except (TypeError, ValueError): return None   # « Bonus Ticket »

def divs(lst):
    pay, win = {}, {}
    for d in lst or []:
        k = str(d["division"]); n = d.get("numberOfWinners") or 0
        win[k] = n; pay[k] = money(d.get("prizeValue")) if n else None
    return pay or None, win or None

def draw(d):
    l = d["lotto"]
    nums = sorted(int(x) for x in l["lottoWinningNumbers"]["numbers"]); b = int(l["lottoWinningNumbers"]["bonusBalls"])
    assert len(nums) == 6 and len(set(nums + [b])) == 7 and all(1 <= n <= 40 for n in nums + [b]), l["drawNumber"]
    pb = d.get("powerBall") or {}; st = d.get("strike") or {}
    p, w = divs(l.get("lottoWinners")); pp, pw = divs(pb.get("powerballWinners")); sp, sw = divs(st.get("strikeWinners"))
    pbn = int(pb["powerballWinningNumber"]) if pb.get("powerballWinningNumber") else None
    if pbn is not None: assert 1 <= pbn <= 14, l["drawNumber"]
    return {"draw": l["drawNumber"], "date": l["drawDate"], "numbers": nums, "bonus": [b], "powerball": pbn,
            "strike": [int(x) for x in st.get("strikeWinningNumbers") or []] or None,
            "payouts": p, "winners": w, "powerballPayouts": pp, "powerballWinners": pw,
            "strikePayouts": sp, "strikeWinners": sw}

def main():
    latest = get("/results/v1/results/lotto")
    assert latest, "API indisponible"
    top = latest["lotto"]["drawNumber"]
    draws = [draw(latest)]
    for n in range(top - 1, top - 30, -1):
        d = get(f"/results/v1/results/lotto/{n}")
        if d: draws.append(draw(d))
        time.sleep(0.5)
    draws.sort(key=lambda x: x["draw"], reverse=True)
    assert len(draws) >= 20, "trop peu de tirages"
    out = {"lotto": draws, "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}
    try:
        nx = get("/draws/lotto")
        if nx: out["nextRaw"] = nx
    except Exception as e:
        print("prochain tirage indisponible :", e, file=sys.stderr)
    new = json.dumps(out, ensure_ascii=False, indent=1)
    old = open("nz_results.json").read() if os.path.exists("nz_results.json") else ""
    def strip(s):
        try: d = json.loads(s); d.pop("updated", None); return d
        except Exception: return None
    if strip(old) != strip(new):
        open("nz_results.json", "w").write(new); print("nz_results.json mis à jour :", draws[0]["draw"], draws[0]["date"])
    else:
        print("aucun changement")
    if os.path.exists("history.json"):
        Hh = json.load(open("history.json")); have = {h["draw"] for h in Hh}; changed = False
        for x in sorted(draws, key=lambda x: x["draw"]):
            if x["draw"] not in have and x["draw"] > max(have):
                Hh.append(x); changed = True
        if changed:
            Hh.sort(key=lambda h: h["draw"]); json.dump(Hh, open("history.json", "w"), ensure_ascii=False, separators=(",", ":"))
            print("history.json :", len(Hh), "tirages")

if __name__ == "__main__":
    main()
