#!/usr/bin/env python3
"""Clippings → Google Drive 單向鏡像（launchd com.user.clippings-drive-sync，每小時）。

設計規格：For_Claude/company/_shared/references/clippings-drive-sync-design-2026-08-01.md
上雲由 Google Drive 桌面版負責，本腳本只保證「vault 來源」與「Drive 掛載點目標」一致。

零依賴（stdlib only）。所有外部路徑集中在 Config，測試可整組指到 tmp 目錄。
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
from dataclasses import dataclass, field

SETTINGS_PLIST = "/Users/fredchu/Library/Preferences/com.google.drivefs.settings.plist"
ACCOUNT_TOKEN = "115170013671149234130"
SOURCE = ("/Users/fredchu/Library/Mobile Documents/iCloud~md~obsidian/"
          "Documents/Clippings/Clippings")
TARGET_RELPATH = "我的雲端硬碟/AI應用研究院/資料/Clippings-by-Fred"
STATE_PATH = "/Users/fredchu/.claude/scripts/clippings-drive-sync.state"
TRASH_ROOT = "/Users/fredchu/.local/state/clippings-drive-sync/trash"
DRIVE_PROC = "/Applications/Google Drive.app/Contents/MacOS/Google Drive"
RSYNC = "/usr/bin/rsync"
EXCLUDES = [".DS_Store", ".obsidian*", ".*.icloud"]

TRASH_RETENTION_DAYS = 30
STALE_HOURS = 3
HIGH_WATER_RATIO = 0.8
ORPHAN_CAP_RATIO = 0.05
ORPHAN_CAP_FLOOR = 3
PLACEHOLDER_WAIT_S = 60
PLACEHOLDER_POLL_S = 5


@dataclass
class Config:
    source: str = SOURCE
    target_relpath: str = TARGET_RELPATH
    settings_plist: str = SETTINGS_PLIST
    account_token: str = ACCOUNT_TOKEN
    state_path: str = STATE_PATH
    trash_root: str = TRASH_ROOT
    drive_proc: str = DRIVE_PROC
    webhook: str = ""
    placeholder_wait_s: int = PLACEHOLDER_WAIT_S
    placeholder_poll_s: int = PLACEHOLDER_POLL_S
    dry_run: bool = False
    alerts: list = field(default_factory=list)


class GuardFailure(Exception):
    """Preflight／刪除閘擋下：本輪中止，不更新 last_success。"""


def post(cfg, msg):
    """告警：Discord webhook（自訂 UA，預設 urllib UA 會被 403 靜默吞）。"""
    cfg.alerts.append(msg)
    if cfg.dry_run:
        print(f"[dry-run 不發送] {msg}")
        return
    print(msg, file=sys.stderr)
    if not cfg.webhook:
        return
    data = json.dumps({"content": msg}).encode()
    req = urllib.request.Request(
        cfg.webhook, data=data,
        headers={"Content-Type": "application/json",
                 "User-Agent": "clippings-drive-sync/1.0"},
    )
    try:
        urllib.request.urlopen(req, timeout=30)
    except Exception as e:
        print(f"Discord push failed: {e}", file=sys.stderr)


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


# ---------------------------------------------------------------- state


def load_state(cfg):
    """回傳 state dict；缺失或無法解析回 None。"""
    try:
        with open(cfg.state_path) as f:
            state = json.load(f)
    except (OSError, ValueError):
        return None
    return state if isinstance(state, dict) else None


def read_state(cfg):
    """回傳 (state, status)。status != "ok" 一律 fail closed（本輪不刪除）。

    missing／corrupt／no_high_water 三態分開，因為處置不同：corrupt 要留證據、
    no_high_water 代表閘 1 的基線不存在（取 or 0 會讓閘形同虛設）。
    """
    if not os.path.exists(cfg.state_path):
        return None, "missing"
    try:
        with open(cfg.state_path) as f:
            state = json.load(f)
    except (OSError, ValueError):
        return None, "corrupt"
    if not isinstance(state, dict):
        return None, "corrupt"
    high_water = state.get("high_water_source_count")
    if isinstance(high_water, bool) or not isinstance(high_water, int) or high_water <= 0:
        return state, "no_high_water"
    return state, "ok"


def quarantine_state(cfg):
    """損毀的 state 搬到 .corrupt-<UTC ts> 保留證據；回傳新路徑（失敗回 None）。"""
    dest = f"{cfg.state_path}.corrupt-{int(now_utc().timestamp())}"
    try:
        shutil.move(cfg.state_path, dest)
    except OSError:
        return None
    return dest


def save_state(cfg, state):
    os.makedirs(os.path.dirname(cfg.state_path), exist_ok=True)
    with open(cfg.state_path, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def parse_ts(value):
    try:
        ts = dt.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=dt.timezone.utc)


# ---------------------------------------------------------------- preflight


def drive_running(cfg):
    """G5：pgrep -f 完整路徑錨定（裸字串會誤匹配 crashpad_handler）。"""
    result = subprocess.run(["pgrep", "-f", cfg.drive_proc], capture_output=True)
    return result.returncode == 0


def resolve_mount_point(cfg):
    """G1：從 drivefs settings 讀指定帳號 token 的 mount_point_path。"""
    try:
        with open(cfg.settings_plist, "rb") as f:
            prefs = plistlib.load(f)
    except (OSError, ValueError) as e:
        raise GuardFailure(f"G1 讀不到 Drive 設定檔 {cfg.settings_plist}：{e}")
    raw = prefs.get("PerAccountPreferences")
    try:
        accounts = json.loads(raw)["per_account_preferences"]
    except (TypeError, ValueError, KeyError) as e:
        raise GuardFailure(f"G1 PerAccountPreferences 解析失敗：{e}")
    for account in accounts:
        if str(account.get("key")) != cfg.account_token:
            continue
        mount = (account.get("value") or {}).get("mount_point_path")
        if not mount:
            raise GuardFailure(f"G1 帳號 {cfg.account_token} 無 mount_point_path")
        if not os.path.isdir(mount):
            raise GuardFailure(f"G1 掛載點不存在：{mount}")
        return mount
    raise GuardFailure(f"G1 設定檔找不到帳號 token {cfg.account_token}")


def check_writable(target):
    """G2：目標實測 touch。EPERM（TCC 拒絕）與 ENOENT（不存在）分開告警。"""
    probe = os.path.join(target, ".clippings-drive-sync.probe")
    try:
        with open(probe, "w") as f:
            f.write("")
        os.unlink(probe)
    except PermissionError as e:
        raise GuardFailure(
            f"G2 目標不可寫（權限被拒，疑似 TCC 未涵蓋 Google Drive domain）："
            f"{target}：{e}")
    except FileNotFoundError as e:
        raise GuardFailure(f"G2 目標目錄不存在：{target}：{e}")
    except OSError as e:
        raise GuardFailure(f"G2 目標 touch 測試失敗：{target}：{e}")


def find_placeholders(root):
    hits = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if fnmatch.fnmatch(name, ".*.icloud"):
                hits.append(os.path.join(dirpath, name))
    return hits


def brctl_download(path):
    subprocess.run(["brctl", "download", path], capture_output=True)


def check_placeholders(cfg, dry_run=False):
    """G4：來源有 .icloud 佔位檔 → brctl download 子資料夾 + 等待重掃。"""
    hits = find_placeholders(cfg.source)
    if not hits:
        return
    if dry_run:
        print(f"[dry-run] 來源有 {len(hits)} 個 .icloud 佔位檔，"
              f"實跑會對 {cfg.source} 執行 brctl download")
        return
    brctl_download(cfg.source)
    deadline = time.monotonic() + cfg.placeholder_wait_s
    while time.monotonic() < deadline:
        time.sleep(cfg.placeholder_poll_s)
        hits = find_placeholders(cfg.source)
        if not hits:
            return
    raise GuardFailure(
        f"G4 來源仍有 {len(hits)} 個 iCloud 佔位檔未 materialize（"
        f"等待 {cfg.placeholder_wait_s}s 後）：\n" + "\n".join(hits[:5]))


# ---------------------------------------------------------------- 檔案清單


def is_excluded(name):
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDES)


def list_files(root):
    """同步／驗證集合：所有未被 exclude 的檔案，相對路徑 → 絕對路徑。"""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not is_excluded(d)]
        for name in filenames:
            if is_excluded(name):
                continue
            full = os.path.join(dirpath, name)
            out[os.path.relpath(full, root)] = full
    return out


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- 刪除閘


FAIL_CLOSED_REASON = {
    "missing": "state 缺失 → fail closed：本輪只新增／更新，不刪除",
    "corrupt": "state 損毀無法解析 → fail closed：本輪只新增／更新，不刪除",
    "no_high_water": ("state 缺 high_water_source_count 基線 → fail closed："
                      "本輪只新增／更新，不刪除"),
}


def evaluate_delete_gate(status, state, source_count, target_count, orphan_count):
    """三道閘。回傳 (allowed, abort, reason)：abort=True 代表本輪中止。"""
    if status != "ok":
        return False, False, FAIL_CLOSED_REASON[status]
    high_water = state["high_water_source_count"]
    floor = high_water * HIGH_WATER_RATIO
    if source_count < floor:
        return False, True, (
            f"high-water mark 擋下：來源 {source_count} 個檔 < 歷史最大 "
            f"{high_water} × {HIGH_WATER_RATIO}（={floor:.1f}）")
    cap = max(ORPHAN_CAP_FLOOR, target_count * ORPHAN_CAP_RATIO)
    if orphan_count > cap:
        return False, True, (
            f"絕對刪除上限擋下：待刪 {orphan_count} 個 > max({ORPHAN_CAP_FLOOR}, "
            f"目標 {target_count} × {ORPHAN_CAP_RATIO})（={cap:.1f}）")
    return True, False, ""


def new_trash_dir(cfg):
    stamp = int(now_utc().timestamp())
    return os.path.join(cfg.trash_root, f"{stamp}-{os.getpid()}")


def prune_trash(cfg):
    """trash 保留 30 天。"""
    cutoff = time.time() - TRASH_RETENTION_DAYS * 86400
    removed = []
    try:
        entries = sorted(os.listdir(cfg.trash_root))
    except OSError:
        return removed
    for name in entries:
        path = os.path.join(cfg.trash_root, name)
        if not os.path.isdir(path):
            continue
        try:
            stamp = int(name.split("-")[0])
        except ValueError:
            stamp = os.path.getmtime(path)
        if stamp < cutoff:
            shutil.rmtree(path, ignore_errors=True)
            removed.append(name)
    return removed


def prune_empty(path):
    for sub in ("deleted", "overwritten"):
        try:
            os.rmdir(os.path.join(path, sub))
        except OSError:
            pass
    try:
        os.rmdir(path)
    except OSError:
        pass


# ---------------------------------------------------------------- sync / verify


def rsync_cmd(source, target, backup_dir, dry_run=False):
    cmd = [RSYNC, "-rlt", "--checksum",
           "--backup", "--backup-dir", backup_dir]
    for pat in EXCLUDES:
        cmd += ["--exclude", pat]
    if dry_run:
        cmd += ["-n", "--itemize-changes"]
    cmd += [source.rstrip("/") + "/", target.rstrip("/") + "/"]
    return cmd


def run_rsync(source, target, backup_dir, dry_run=False):
    cmd = rsync_cmd(source, target, backup_dir, dry_run)
    # launchd 無 LANG 時 openrsync 對中文檔名輸出可能非合法 UTF-8，
    # 嚴格解碼會炸 UnicodeDecodeError；itemize 輸出僅供人讀，replace 兜底
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def verify(source, target):
    """V1 檔案清單對拍 + V2 逐檔 md5。回傳差異 dict（空 = 全綠）。"""
    src = list_files(source)
    dst = list_files(target)
    only_source = sorted(set(src) - set(dst))
    only_target = sorted(set(dst) - set(src))
    mismatch = []
    for rel in sorted(set(src) & set(dst)):
        try:
            if md5(src[rel]) != md5(dst[rel]):
                mismatch.append(rel)
        except OSError as e:
            mismatch.append(f"{rel}（讀取失敗：{e}）")
    diff = {}
    if only_source:
        diff["only_source"] = only_source
    if only_target:
        diff["only_target"] = only_target
    if mismatch:
        diff["md5_mismatch"] = mismatch
    return diff


def format_diff(diff):
    lines = []
    for key, items in diff.items():
        lines.append(f"{key}（{len(items)}）：" + "、".join(items[:5])
                     + ("…" if len(items) > 5 else ""))
    return "\n".join(lines)


def check_stale(cfg, state):
    """落後偵測：last_success 落後 > 3h（含從未成功）→ 告警。"""
    last = parse_ts((state or {}).get("last_success"))
    if last is None:
        post(cfg, "⚠️ clippings-drive-sync：尚無成功紀錄（last_success 缺失）")
        return
    behind = now_utc() - last
    if behind > dt.timedelta(hours=STALE_HOURS):
        post(cfg, f"⚠️ clippings-drive-sync：上次成功同步是 "
                  f"{last.astimezone():%m-%d %H:%M}，落後 "
                  f"{behind.total_seconds() / 3600:.1f} 小時")


# ---------------------------------------------------------------- 主流程


def run(cfg, dry_run=False):
    """外層：未預期例外也要走完告警三件套（Drive FUSE I/O 錯誤、磁碟寫入失敗等）。"""
    cfg.dry_run = dry_run
    try:
        return _run(cfg, dry_run)
    except Exception as e:
        post(cfg, f"🛑 clippings-drive-sync 未預期例外，本輪中止："
                  f"{type(e).__name__}: {e}\n"
                  f"{traceback.format_exc().strip()[-800:]}")
        try:
            check_stale(cfg, read_state(cfg)[0])
        except Exception as stale_err:
            print(f"check_stale failed: {stale_err}", file=sys.stderr)
        return 1


def _run(cfg, dry_run=False):
    state, status = read_state(cfg)
    if status != "ok":
        # 無條件告警：閘 3 觸發與否不能取決於本輪剛好有沒有 orphan
        detail = ""
        if status == "corrupt":
            backup = None if dry_run else quarantine_state(cfg)
            detail = (f"，已備份至 {backup}" if backup else
                      "，備份失敗（原檔將被覆寫）" if not dry_run else "")
            state = None
        if status in ("missing", "corrupt"):
            detail += "；high_water 基線將以本輪來源檔數重建，若來源正處於縮水窗口" \
                      "（iCloud 未 materialize 等），基線會偏低，請人工核對"
        post(cfg, f"⚠️ clippings-drive-sync：{FAIL_CLOSED_REASON[status]}{detail}")

    if not dry_run:
        working = dict(state or {})
        working["last_attempt"] = now_utc().isoformat()
        save_state(cfg, working)

    if not drive_running(cfg):
        # G5：靜默跳過本輪，不告警、不更新 last_success（落後偵測會撈到）
        print("G5 Google Drive 未執行，跳過本輪", file=sys.stderr)
        check_stale(cfg, state)
        return 0

    try:
        mount = resolve_mount_point(cfg)
        target = os.path.join(mount, cfg.target_relpath)
        check_writable(target)
        check_placeholders(cfg, dry_run)
    except GuardFailure as e:
        post(cfg, f"🛑 clippings-drive-sync preflight 中止：{e}")
        check_stale(cfg, state)
        return 1

    src_files = list_files(cfg.source)
    dst_files = list_files(target)
    orphans = sorted(set(dst_files) - set(src_files))
    allowed, abort, reason = evaluate_delete_gate(
        status, state, len(src_files), len(dst_files), len(orphans))

    if abort:
        post(cfg, f"🛑 clippings-drive-sync 刪除閘中止：{reason}\n"
                  f"待刪清單（{len(orphans)}）：\n" + "\n".join(orphans[:20]))
        check_stale(cfg, state)
        return 1
    if not allowed and orphans:
        post(cfg, f"⚠️ clippings-drive-sync：{reason}\n"
                  f"未刪除的 orphan（{len(orphans)}）：\n" + "\n".join(orphans[:20]))

    trash = new_trash_dir(cfg)
    deleted_dir = os.path.join(trash, "deleted")
    overwritten_dir = os.path.join(trash, "overwritten")

    if dry_run:
        print(f"來源 {len(src_files)} 檔／目標 {len(dst_files)} 檔")
        print(f"刪除閘：{'放行' if allowed else '擋下'}"
              + (f"（{reason}）" if reason else ""))
        print(f"orphan（{len(orphans)}）：\n" + "\n".join(orphans) if orphans
              else "orphan：無")
        result = run_rsync(cfg.source, target, overwritten_dir, dry_run=True)
        print(f"--- rsync -n --itemize-changes（rc={result.returncode}）---")
        print(result.stdout.strip() or "(無變更)")
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        diff = verify(cfg.source, target)
        print("--- 現況 md5 對拍 ---")
        print(format_diff(diff) if diff else "兩端一致")
        return 0

    deleted = []
    if allowed and orphans:
        os.makedirs(deleted_dir, exist_ok=True)
        for rel in orphans:
            dest = os.path.join(deleted_dir, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(dst_files[rel], dest)
            deleted.append(rel)

    os.makedirs(overwritten_dir, exist_ok=True)
    result = run_rsync(cfg.source, target, overwritten_dir)
    prune_empty(trash)
    prune_trash(cfg)

    state = load_state(cfg) or {}
    state["last_attempt"] = now_utc().isoformat()
    state["source_count"] = len(src_files)
    state["target_count"] = len(list_files(target))
    state["deleted_count"] = len(deleted)
    state["high_water_source_count"] = max(
        state.get("high_water_source_count") or 0, len(src_files))

    if result.returncode != 0:
        state["last_error"] = (result.stderr or result.stdout).strip()[:500]
        save_state(cfg, state)
        post(cfg, f"🛑 clippings-drive-sync rsync 失敗（rc={result.returncode}）：\n"
                  f"{state['last_error']}")
        check_stale(cfg, state)
        return 1

    diff = verify(cfg.source, target)
    state["diff_summary"] = {k: len(v) for k, v in diff.items()}
    if diff:
        state["last_error"] = format_diff(diff)[:500]
        save_state(cfg, state)
        note = f"\n（本輪刪除閘擋下，orphan 未刪：{reason}）" if not allowed else ""
        post(cfg, f"🛑 clippings-drive-sync verify 不一致，本輪失敗：\n"
                  f"{format_diff(diff)}{note}")
        check_stale(cfg, state)
        return 1

    state.pop("last_error", None)
    state["last_success"] = now_utc().isoformat()
    save_state(cfg, state)
    print(f"OK：{len(src_files)} 檔同步、刪除 {len(deleted)} 檔")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Clippings → Google Drive 單向鏡像（preflight／軟刪除／md5 驗證）")
    parser.add_argument("--dry-run", action="store_true",
                        help="跑完整 preflight，印 orphan 清單、rsync 預覽與 md5 對拍，不寫入")
    args = parser.parse_args(argv)
    cfg = Config(webhook=os.environ.get("DISCORD_WEBHOOK", ""))
    return run(cfg, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
