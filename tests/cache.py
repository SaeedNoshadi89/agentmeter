#!/usr/bin/env python3
"""Tests for how AgentMeter caches and backs off:  python3 tests/cache.py

Uses fake fetchers and a temporary cache, so it makes no network calls.
"""
import importlib.machinery, importlib.util, json, os, sys, tempfile, time

sys.dont_write_bytecode = True
T = tempfile.mkdtemp()
os.environ["AGENTMETER_CACHE"] = os.path.join(T, "cache.json")
sys.argv = ["agentmeter"]
HERE = os.path.dirname(os.path.abspath(__file__))
loader = importlib.machinery.SourceFileLoader("am", os.path.join(HERE, "..", "agentmeter"))
m = importlib.util.module_from_spec(importlib.util.spec_from_loader("am", loader))
loader.exec_module(m)
passed = failed = 0


def ok(name, cond):
    global passed, failed
    passed, failed = passed + bool(cond), failed + (not cond)
    print(("  ok    " if cond else "  FAIL  ") + name)


calls = {"n": 0}
state = {}


def good():
    calls["n"] += 1
    return {"meters": [m.meter("5-hour", 30, time.time() + 3600)]}


def limited():
    calls["n"] += 1
    e = m.FetchError("rate limited, retrying soon", retry_in=60)
    e.rate_limited = True
    raise e


m.jobs_for = lambda dirs: [("claude:default", "claude", "Claude Code", "a@example.com", state["fn"])]


def age(seconds):
    c = json.load(open(m.CACHE))
    c["claude:default"]["at"] -= seconds
    json.dump(c, open(m.CACHE, "w"))


def wait_left():
    return json.load(open(m.CACHE))["claude:default"]["retry_at"] - time.time()


def end_backoff():
    c = json.load(open(m.CACHE))
    c["claude:default"]["retry_at"] = time.time() - 1
    json.dump(c, open(m.CACHE, "w"))


state["fn"] = good
d = m.collect()
ok("a good check records when it happened", d["claude:default"].get("checked_at"))
n = calls["n"]; age(120); m.collect()
ok("Claude isn't asked again after 2 minutes", calls["n"] == n)
age(200); m.collect()
ok("Claude is asked again after 5 minutes", calls["n"] == n + 1)

state["fn"] = limited
age(400); d = m.collect()
ok("a 429 keeps the last good numbers", d["claude:default"]["meters"] and d["claude:default"]["stale"])
first = wait_left()
ok("first wait after a 429 is 5 minutes", 290 < first <= 300)
n = calls["n"]; m.collect(); m.collect(fresh=True)
ok("no requests during the wait, even when refreshing by hand", calls["n"] == n)
end_backoff(); m.collect()
ok("a second 429 waits 10 minutes", 590 < wait_left() <= 600)
end_backoff(); m.collect()
ok("a third 429 waits 20 minutes", 1190 < wait_left() <= 1200)
for _ in range(6):
    end_backoff(); m.collect()
ok("the wait stops growing at an hour", 3590 < wait_left() <= 3600)
state["fn"] = good
end_backoff(); d = m.collect()
ok("success clears the wait and the stale mark", "stale" not in d["claude:default"] and "retry_at" not in json.load(open(m.CACHE))["claude:default"])
end = json.load(open(m.CACHE))["claude:default"]
ok("success resets the back-off count", "fails" not in end)

c = json.load(open(m.CACHE))
c["claude:default"]["data"]["meters"][0]["resets_at"] = time.time() - 5
json.dump(c, open(m.CACHE, "w"))
n = calls["n"]; m.collect()
ok("a passed reset time triggers a new check", calls["n"] == n + 1)

c = json.load(open(m.CACHE))
c["claude:/no/such/folder"] = {"at": time.time(), "data": {"error": "x", "agent": "claude"}}
m.save_cache(c)
ok("entries for missing folders are cleaned up", "claude:/no/such/folder" not in json.load(open(m.CACHE)))

view, cache = {}, {}
m.use_claude_code_limits({"rate_limits": {"five_hour": {"used_percentage": 10, "resets_at": time.time() + 60}}}, "claude:x", None, view, cache, time.time())
ok("status line data with one window works", view["claude:x"]["meters"][0]["left"] == 90)
view2 = {"claude:x": view["claude:x"]}
m.use_claude_code_limits({"rate_limits": {"seven_day": {"used_percentage": 50, "resets_at": time.time() + 60}}}, "claude:x", None, view2, {}, time.time())
ok("a window Claude Code omits keeps its last value", [x["label"] for x in view2["claude:x"]["meters"]] == ["5-hour", "Weekly"])
before = dict(view2)
m.use_claude_code_limits({}, "claude:x", None, view2, {}, time.time())
m.use_claude_code_limits({"rate_limits": "nonsense"}, "claude:x", None, view2, {}, time.time())
ok("missing or odd status line data changes nothing", view2 == before)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
