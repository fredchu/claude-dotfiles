#!/usr/bin/env python3
"""clippings_drive_sync 單元測試（全部指向 tmp 目錄，不碰真實路徑、不發網路請求）。"""
import glob
import io
import json
import os
import plistlib
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import clippings_drive_sync as mod  # noqa: E402

TOKEN = "115170013671149234130"


def write_settings(path, token, mount):
    payload = {"per_account_preferences": [
        {"key": "999", "value": {"mount_point_path": "/nonexistent/other"}},
        {"key": token, "value": {"mount_point_path": mount}},
    ]}
    with open(path, "wb") as f:
        plistlib.dump({"PerAccountPreferences": json.dumps(payload)}, f)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        self.source = os.path.join(root, "source")
        self.mount = os.path.join(root, "mount")
        self.target = os.path.join(self.mount, "rel", "Clippings-by-Fred")
        self.settings = os.path.join(root, "drivefs.settings.plist")
        os.makedirs(self.source)
        os.makedirs(self.target)
        write_settings(self.settings, TOKEN, self.mount)
        self.cfg = mod.Config(
            source=self.source,
            target_relpath="rel/Clippings-by-Fred",
            settings_plist=self.settings,
            account_token=TOKEN,
            state_path=os.path.join(root, "state.json"),
            trash_root=os.path.join(root, "trash"),
            drive_proc="/nonexistent/Google Drive",
            webhook="",
            placeholder_wait_s=0,
            placeholder_poll_s=0,
        )
        self.addCleanup(self.tmp.cleanup)

    def put(self, root, name, body):
        path = os.path.join(root, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(body)
        return path

    def run_sync(self, dry_run=False, drive_up=True):
        buf = io.StringIO()
        with mock.patch.object(mod, "drive_running", lambda cfg: drive_up), \
                redirect_stdout(buf):
            rc = mod.run(self.cfg, dry_run=dry_run)
        return rc, buf.getvalue()


class TestG1MountResolution(Base):
    def test_resolves_token_mount_point(self):
        self.assertEqual(mod.resolve_mount_point(self.cfg), self.mount)

    def test_missing_token_fails(self):
        self.cfg.account_token = "000000"
        with self.assertRaises(mod.GuardFailure) as ctx:
            mod.resolve_mount_point(self.cfg)
        self.assertIn("000000", str(ctx.exception))

    def test_mount_path_gone_fails(self):
        write_settings(self.settings, TOKEN, os.path.join(self.tmp.name, "gone"))
        with self.assertRaises(mod.GuardFailure) as ctx:
            mod.resolve_mount_point(self.cfg)
        self.assertIn("掛載點不存在", str(ctx.exception))

    def test_unparseable_prefs_fails(self):
        with open(self.settings, "wb") as f:
            plistlib.dump({"PerAccountPreferences": "not json"}, f)
        with self.assertRaises(mod.GuardFailure):
            mod.resolve_mount_point(self.cfg)


class TestG2Writable(Base):
    def test_writable_target_passes(self):
        mod.check_writable(self.target)

    def test_missing_target_is_enoent(self):
        with self.assertRaises(mod.GuardFailure) as ctx:
            mod.check_writable(os.path.join(self.tmp.name, "nope"))
        self.assertIn("不存在", str(ctx.exception))

    def test_unwritable_target_is_eperm(self):
        if os.geteuid() == 0:
            self.skipTest("root 會繞過權限檢查")
        os.chmod(self.target, 0o500)
        self.addCleanup(os.chmod, self.target, 0o700)
        with self.assertRaises(mod.GuardFailure) as ctx:
            mod.check_writable(self.target)
        self.assertIn("權限被拒", str(ctx.exception))


class TestG4Placeholders(Base):
    def test_no_placeholders_passes(self):
        self.put(self.source, "a.md", "x")
        with mock.patch.object(mod, "brctl_download") as brctl:
            mod.check_placeholders(self.cfg)
        brctl.assert_not_called()

    def test_placeholder_survives_download_aborts(self):
        self.put(self.source, ".a.md.icloud", "")
        with mock.patch.object(mod, "brctl_download") as brctl:
            with self.assertRaises(mod.GuardFailure) as ctx:
                mod.check_placeholders(self.cfg)
        brctl.assert_called_once_with(self.source)
        self.assertIn("佔位檔", str(ctx.exception))

    def test_dry_run_does_not_download(self):
        self.put(self.source, ".a.md.icloud", "")
        with mock.patch.object(mod, "brctl_download") as brctl, \
                redirect_stdout(io.StringIO()):
            mod.check_placeholders(self.cfg, dry_run=True)
        brctl.assert_not_called()


class TestDeleteGate(unittest.TestCase):
    def test_geometric_shrink_blocked(self):
        state = {"high_water_source_count": 63}
        allowed, abort, reason = mod.evaluate_delete_gate("ok", state, 32, 63, 31)
        self.assertFalse(allowed)
        self.assertTrue(abort)
        self.assertIn("high-water", reason)

    def test_within_high_water_passes(self):
        state = {"high_water_source_count": 63}
        allowed, abort, _ = mod.evaluate_delete_gate("ok", state, 60, 62, 2)
        self.assertTrue(allowed)
        self.assertFalse(abort)

    def test_orphan_cap_blocks_bulk_delete(self):
        state = {"high_water_source_count": 100}
        allowed, abort, reason = mod.evaluate_delete_gate("ok", state, 100, 100, 10)
        self.assertFalse(allowed)
        self.assertTrue(abort)
        self.assertIn("絕對刪除上限", reason)

    def test_orphan_cap_floor_is_three(self):
        state = {"high_water_source_count": 10}
        self.assertTrue(mod.evaluate_delete_gate("ok", state, 10, 10, 3)[0])
        self.assertFalse(mod.evaluate_delete_gate("ok", state, 10, 10, 4)[0])

    def test_every_non_ok_status_fails_closed_without_abort(self):
        for status in ("missing", "corrupt", "no_high_water"):
            allowed, abort, reason = mod.evaluate_delete_gate(
                status, None, 63, 63, 5)
            self.assertFalse(allowed, status)
            self.assertFalse(abort, status)
            self.assertIn("fail closed", reason)


class TestReadState(Base):
    def test_missing_file(self):
        self.assertEqual(mod.read_state(self.cfg), (None, "missing"))

    def test_corrupt_json(self):
        with open(self.cfg.state_path, "w") as f:
            f.write("{not json")
        self.assertEqual(mod.read_state(self.cfg), (None, "corrupt"))

    def test_non_dict_json(self):
        with open(self.cfg.state_path, "w") as f:
            f.write("[1, 2]")
        self.assertEqual(mod.read_state(self.cfg), (None, "corrupt"))

    def test_missing_high_water_key(self):
        mod.save_state(self.cfg, {"last_success": "2026-08-06T00:00:00+00:00"})
        state, status = mod.read_state(self.cfg)
        self.assertEqual(status, "no_high_water")
        self.assertIn("last_success", state)

    def test_zero_or_bool_high_water_is_not_a_baseline(self):
        for bad in (0, -1, True, "63", None):
            mod.save_state(self.cfg, {"high_water_source_count": bad})
            self.assertEqual(mod.read_state(self.cfg)[1], "no_high_water", bad)

    def test_valid_state_is_ok(self):
        mod.save_state(self.cfg, {"high_water_source_count": 63})
        state, status = mod.read_state(self.cfg)
        self.assertEqual(status, "ok")
        self.assertEqual(state["high_water_source_count"], 63)


class TestVerify(Base):
    def test_identical_trees_are_clean(self):
        self.put(self.source, "a.md", "hello")
        self.put(self.target, "a.md", "hello")
        self.assertEqual(mod.verify(self.source, self.target), {})

    def test_same_size_different_content_is_mismatch(self):
        self.put(self.source, "a.md", "hello")
        self.put(self.target, "a.md", "world")
        self.assertEqual(mod.verify(self.source, self.target),
                         {"md5_mismatch": ["a.md"]})

    def test_extra_target_file_reported(self):
        self.put(self.source, "a.md", "x")
        self.put(self.target, "a.md", "x")
        self.put(self.target, "orphan.md", "x")
        self.assertEqual(mod.verify(self.source, self.target),
                         {"only_target": ["orphan.md"]})

    def test_excluded_names_ignored(self):
        self.put(self.source, "a.md", "x")
        self.put(self.target, "a.md", "x")
        self.put(self.target, ".DS_Store", "junk")
        self.put(self.source, ".a.md.icloud", "")
        self.assertEqual(mod.verify(self.source, self.target), {})


class TestTrashRetention(Base):
    def test_prunes_older_than_30_days(self):
        old = int(time.time()) - 31 * 86400
        fresh = int(time.time()) - 86400
        for stamp in (old, fresh):
            os.makedirs(os.path.join(self.cfg.trash_root, f"{stamp}-123", "deleted"))
        removed = mod.prune_trash(self.cfg)
        self.assertEqual(removed, [f"{old}-123"])
        self.assertTrue(os.path.isdir(
            os.path.join(self.cfg.trash_root, f"{fresh}-123")))


class TestRsyncCommand(unittest.TestCase):
    def test_flags_match_openrsync_support(self):
        cmd = mod.rsync_cmd("/s", "/t", "/trash/overwritten")
        self.assertIn("--checksum", cmd)
        self.assertIn("-rlt", cmd)
        self.assertNotIn("-a", cmd)
        self.assertNotIn("--delete", cmd)
        self.assertFalse([c for c in cmd if c.startswith("--info")])
        self.assertEqual(cmd[-2:], ["/s/", "/t/"])


class TestRun(Base):
    def test_happy_path_syncs_deletes_and_marks_success(self):
        for name in ("a.md", "b.md", "c.md"):
            self.put(self.source, name, name)
        self.put(self.target, "a.md", "a.md")
        self.put(self.target, "gone.md", "old")
        mod.save_state(self.cfg, {"high_water_source_count": 3})

        rc, _ = self.run_sync()

        self.assertEqual(rc, 0)
        self.assertEqual(mod.verify(self.source, self.target), {})
        self.assertFalse(os.path.exists(os.path.join(self.target, "gone.md")))
        trashed = [os.path.join(dirpath, n)
                   for dirpath, _, names in os.walk(self.cfg.trash_root)
                   for n in names]
        self.assertEqual([os.path.basename(p) for p in trashed], ["gone.md"])
        state = mod.load_state(self.cfg)
        self.assertIn("last_success", state)
        self.assertEqual(state["source_count"], 3)
        self.assertEqual(state["deleted_count"], 1)

    def test_overwritten_file_goes_to_trash(self):
        self.put(self.source, "a.md", "new")
        self.put(self.target, "a.md", "old")
        mod.save_state(self.cfg, {"high_water_source_count": 1})

        rc, _ = self.run_sync()

        self.assertEqual(rc, 0)
        backups = [n for _, _, names in os.walk(self.cfg.trash_root) for n in names]
        self.assertEqual(backups, ["a.md"])

    def test_missing_state_does_not_delete_and_fails_round(self):
        self.put(self.source, "a.md", "x")
        self.put(self.target, "a.md", "x")
        self.put(self.target, "orphan.md", "x")

        rc, _ = self.run_sync()

        self.assertEqual(rc, 1)
        self.assertTrue(os.path.exists(os.path.join(self.target, "orphan.md")))
        state = mod.load_state(self.cfg)
        self.assertNotIn("last_success", state)
        self.assertEqual(state["high_water_source_count"], 1)
        self.assertTrue(any("fail closed" in a for a in self.cfg.alerts))

    def test_high_water_shrink_aborts_before_touching_target(self):
        self.put(self.source, "a.md", "x")
        for i in range(10):
            self.put(self.target, f"f{i}.md", "x")
        mod.save_state(self.cfg, {"high_water_source_count": 63,
                                  "last_success": mod.now_utc().isoformat()})

        rc, _ = self.run_sync()

        self.assertEqual(rc, 1)
        self.assertEqual(len(mod.list_files(self.target)), 10)
        self.assertFalse(os.path.exists(os.path.join(self.target, "a.md")))
        self.assertTrue(any("high-water" in a for a in self.cfg.alerts))

    def test_verify_mismatch_fails_round(self):
        self.put(self.source, "a.md", "x")
        self.put(self.target, "a.md", "x")
        mod.save_state(self.cfg, {"high_water_source_count": 1})
        with mock.patch.object(mod, "verify", return_value={"md5_mismatch": ["a.md"]}):
            rc, _ = self.run_sync()
        self.assertEqual(rc, 1)
        state = mod.load_state(self.cfg)
        self.assertNotIn("last_success", state)
        self.assertTrue(any("verify 不一致" in a for a in self.cfg.alerts))

    def test_drive_down_skips_silently(self):
        self.put(self.source, "a.md", "x")
        stamp = mod.now_utc().isoformat()
        mod.save_state(self.cfg, {"high_water_source_count": 1,
                                  "last_success": stamp})

        rc, _ = self.run_sync(drive_up=False)

        self.assertEqual(rc, 0)
        state = mod.load_state(self.cfg)
        self.assertEqual(state["last_success"], stamp)
        self.assertIn("last_attempt", state)
        self.assertFalse(os.path.exists(os.path.join(self.target, "a.md")))
        self.assertEqual(self.cfg.alerts, [])

    def test_stale_last_success_alerts(self):
        self.put(self.source, "a.md", "x")
        stale = (mod.now_utc() - mod.dt.timedelta(hours=5)).isoformat()
        mod.save_state(self.cfg, {"high_water_source_count": 1,
                                  "last_success": stale})

        self.run_sync(drive_up=False)

        self.assertTrue(any("落後" in a for a in self.cfg.alerts))

    def test_rsync_failure_marks_round_failed(self):
        self.put(self.source, "a.md", "x")
        mod.save_state(self.cfg, {"high_water_source_count": 1})
        boom = subprocess.CompletedProcess([], 23, stdout="", stderr="rsync: boom")
        with mock.patch.object(mod, "run_rsync", return_value=boom):
            rc, _ = self.run_sync()
        self.assertEqual(rc, 1)
        state = mod.load_state(self.cfg)
        self.assertNotIn("last_success", state)
        self.assertIn("boom", state["last_error"])
        self.assertTrue(any("rsync 失敗" in a for a in self.cfg.alerts))

    def test_unexpected_exception_still_alerts(self):
        self.put(self.source, "a.md", "x")
        mod.save_state(self.cfg, {"high_water_source_count": 1,
                                  "last_success": mod.now_utc().isoformat()})
        with mock.patch.object(mod, "list_files", side_effect=OSError("FUSE 掛了")):
            rc, _ = self.run_sync()
        self.assertEqual(rc, 1)
        self.assertEqual(len(self.cfg.alerts), 1)
        self.assertIn("未預期例外", self.cfg.alerts[0])
        self.assertIn("FUSE 掛了", self.cfg.alerts[0])

    def test_corrupt_state_is_quarantined_and_blocks_delete(self):
        self.put(self.source, "a.md", "x")
        self.put(self.target, "a.md", "x")
        self.put(self.target, "orphan.md", "x")
        with open(self.cfg.state_path, "w") as f:
            f.write("{not json")

        rc, _ = self.run_sync()

        self.assertEqual(rc, 1)
        self.assertTrue(os.path.exists(os.path.join(self.target, "orphan.md")))
        backups = glob.glob(self.cfg.state_path + ".corrupt-*")
        self.assertEqual(len(backups), 1)
        with open(backups[0]) as f:
            self.assertEqual(f.read(), "{not json")
        self.assertTrue(any("損毀" in a for a in self.cfg.alerts))
        self.assertEqual(mod.load_state(self.cfg)["high_water_source_count"], 1)

    def test_corrupt_state_alerts_even_with_no_orphans(self):
        self.put(self.source, "a.md", "x")
        self.put(self.target, "a.md", "x")
        with open(self.cfg.state_path, "w") as f:
            f.write("{not json")

        rc, _ = self.run_sync()

        self.assertEqual(rc, 0)
        self.assertTrue(any("損毀" in a for a in self.cfg.alerts))
        self.assertIn("last_success", mod.load_state(self.cfg))

    def test_missing_high_water_key_fails_closed(self):
        self.put(self.source, "a.md", "x")
        self.put(self.target, "a.md", "x")
        self.put(self.target, "orphan.md", "x")
        mod.save_state(self.cfg, {"last_success": mod.now_utc().isoformat()})

        rc, _ = self.run_sync()

        self.assertEqual(rc, 1)
        self.assertTrue(os.path.exists(os.path.join(self.target, "orphan.md")))
        # 必須是「閘 3 明示 fail closed」，不是靠 KeyError 撞出來的例外
        self.assertFalse(any("未預期例外" in a for a in self.cfg.alerts))
        self.assertTrue(any("high_water_source_count" in a and "fail closed" in a
                            for a in self.cfg.alerts))

    def test_dry_run_makes_no_network_call(self):
        self.put(self.source, "a.md", "x")
        self.cfg.webhook = "https://example.invalid/hook"
        with mock.patch.object(mod.urllib.request, "urlopen") as urlopen:
            rc, out = self.run_sync(dry_run=True)
        urlopen.assert_not_called()
        self.assertEqual(rc, 0)
        self.assertIn("[dry-run 不發送]", out)
        self.assertTrue(any("fail closed" in a for a in self.cfg.alerts))

    def test_dry_run_writes_nothing(self):
        self.put(self.source, "a.md", "new")
        self.put(self.target, "a.md", "old")
        self.put(self.target, "orphan.md", "x")
        mod.save_state(self.cfg, {"high_water_source_count": 1})
        before = mod.load_state(self.cfg)

        rc, out = self.run_sync(dry_run=True)

        self.assertEqual(rc, 0)
        self.assertEqual(mod.load_state(self.cfg), before)
        self.assertFalse(os.path.exists(self.cfg.trash_root))
        with open(os.path.join(self.target, "a.md")) as f:
            self.assertEqual(f.read(), "old")
        self.assertTrue(os.path.exists(os.path.join(self.target, "orphan.md")))
        self.assertIn("orphan.md", out)
        self.assertIn("md5 對拍", out)


if __name__ == "__main__":
    unittest.main()
