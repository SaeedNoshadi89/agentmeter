#!/usr/bin/env python3
"""Offline regression tests for recorded usage and footer rendering."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("agentmeter", str(ROOT / "agentmeter"))
am = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
loader.exec_module(am)


class AccuracyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"CODEX_HOME": str(self.home)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.now = time.time()

    def event(self, used, at=None, limit_id="codex", minutes=300):
        return {"timestamp": am.datetime.fromtimestamp(at or self.now, am.timezone.utc).isoformat(),
                "payload": {"rate_limits": {"limit_id": limit_id,
                    "primary": {"used_percent": used, "window_minutes": minutes,
                                "resets_at": self.now + 3600}}}}

    def session(self, name, events, modified=None):
        p = self.home / "sessions/2026/11/07" / f"rollout-{name}.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(json.dumps(e) if isinstance(e, dict) else e for e in events) + "\n")
        if modified:
            os.utime(p, (modified, modified))
        return p

    def test_event_time_wins_over_file_modification(self):
        self.session("new", [self.event(65)], self.now - 500)
        self.session("touched-old", [self.event(10, self.now - 100)], self.now)
        result = am.codex()
        self.assertEqual(result["meters"][0]["left"], 35)
        self.assertAlmostEqual(result["as_of"], self.now, places=4)

    def test_no_twenty_session_cutoff(self):
        self.session("real", [self.event(77)], self.now - 1000)
        for i in range(25):
            self.session(str(i), [{"payload": {"rate_limits": None}}], self.now)
        self.assertEqual(am.codex()["meters"][0]["used"], 77)

    def test_partial_null_and_other_limit_events_do_not_hide_usage(self):
        self.session("mixed", [self.event(42), self.event(99, limit_id="other-model"),
                    {"payload": {"rate_limits": None}}, '{"rate_limits":'])
        self.assertEqual(am.codex()["meters"][0]["used"], 42)

    def test_unknown_window_keeps_its_duration(self):
        self.session("daily", [self.event(25, minutes=1440)])
        self.assertEqual(am.codex()["meters"][0]["label"], "1440-minute")

    def test_reverse_reader_handles_chunk_boundaries(self):
        p = self.session("long", [self.event(30), {"text": "a" * 150000}])
        lines = list(am.reversed_lines(p))
        self.assertEqual(json.loads(lines[-1])["payload"]["rate_limits"]["primary"]["used_percent"], 30)
        self.assertEqual(am.codex()["meters"][0]["used"], 30)

    def test_expired_window_is_unknown_in_all_views(self):
        value = am.meter("5-hour", 95, self.now - 10)
        self.assertIsNone(value["left"])
        self.assertTrue(value["expired"])
        lines = "\n".join(am.lines_for({"codex": {"agent": "codex", "meters": [value]}}, 10))
        self.assertIn("awaiting update", lines)
        self.assertNotIn("100%", lines)

    def test_cached_json_during_backoff_also_expires(self):
        data = {"agent": "codex", "meters": [{"label": "5-hour", "used": 95,
                "left": 5, "resets_at": self.now - 10}]}
        entry = {"at": self.now, "data": data, "retry_at": self.now + 500}
        with patch.object(am, "load_cache", return_value={"codex": entry}), \
                patch.object(am, "save_cache"), \
                patch.object(am, "jobs_for", return_value=[("codex", "codex", "Codex", None, None)]):
            result = am.collect()
        self.assertIsNone(result["codex"]["meters"][0]["left"])
        self.assertTrue(result["codex"]["meters"][0]["expired"])

    def footer(self, data, args=None):
        stream = io.StringIO()
        with patch.object(am, "cached_view", return_value=data), \
                patch.object(am, "claude_email", return_value=None), \
                patch.object(am, "load_cache", return_value={}), \
                patch.object(am, "refresh_in_background"), \
                patch.object(am.sys, "stdin", io.StringIO("{}")), \
                patch.object(am.sys, "argv", ["agentmeter", "statusline"] + (args or [])), \
                contextlib.redirect_stdout(stream):
            am.statusline()
        return stream.getvalue()

    def test_brand_icons_and_plain_fallback(self):
        data = {"claude:default": {"agent": "claude", "meters": []},
                "codex": {"agent": "codex", "meters": []}}
        out = self.footer(data, ["--nerd-icons"])
        self.assertIn("\uec82", out)
        self.assertIn("\uec81", out)
        self.assertNotIn("\033_G", out)  # no terminal image protocol in a TUI footer
        plain = self.footer(data, ["--no-icons"])
        self.assertIn("✻", plain)
        self.assertIn(">_", plain)
        self.assertNotIn("\uec81", plain)
        default = self.footer(data)
        self.assertIn("Claude", default)
        self.assertIn("Codex", default)
        self.assertNotIn("\uec81", default)
        self.assertNotIn("\uec82", default)

    def test_footer_exposes_failed_checks(self):
        out = self.footer({"codex": {"agent": "codex", "stale": "offline",
                          "meters": [am.meter("5-hour", 30, self.now + 500)]}})
        self.assertIn("stale: offline", out)

    def test_reset_only_change_is_saved(self):
        old = am.meter("5-hour", 30, self.now + 100)
        view = {"claude:x": {"meters": [old]}}
        cache = {"claude:x": {"at": self.now, "data": view["claude:x"]}}
        payload = {"rate_limits": {"five_hour": {"used_percentage": 30,
                                               "resets_at": self.now + 500}}}
        with patch.object(am, "save_cache") as save, \
                patch.object(am, "claude_email", return_value=None):
            am.use_claude_code_limits(payload, "claude:x", None, view, cache, self.now)
        save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
