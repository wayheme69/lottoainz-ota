import json, urllib.request, time
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
B = "https://pathway.mylotto.co.nz/api/results/v1/results/lotto"
out = {}
for n in ["", "/2628", "/2000", "/1500", "/1000", "/500", "/100", "/1"]:
    try:
        r = urllib.request.urlopen(urllib.request.Request(B + n, headers={"User-Agent": UA, "Accept": "application/json", "Origin": "https://mylotto.co.nz", "Referer": "https://mylotto.co.nz/"}), timeout=40)
        d = json.loads(r.read().decode())
        l = d.get("lotto", {})
        out[n or "latest"] = {"status": r.status, "draw": l.get("drawNumber"), "date": l.get("drawDate"), "nums": l.get("lottoWinningNumbers"), "divs": len(l.get("lottoWinners") or []), "pb": (d.get("powerBall") or {}).get("powerballWinningNumber")}
    except Exception as e:
        out[n or "latest"] = {"error": str(e)[:200]}
    time.sleep(1)
json.dump(out, open("probe.json", "w"), indent=1)
print(json.dumps(out, indent=1))
