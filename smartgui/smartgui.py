#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import queue
import re
import shutil
import subprocess
import threading
from datetime import datetime
from tkinter import (
    Tk, TOP, BOTTOM, LEFT, RIGHT, X, BOTH, END, HORIZONTAL, filedialog, messagebox, W
)
from tkinter import ttk

APP_TITLE = "SMART Monitor (Tkinter)"
APP_MIN_W = 1120
APP_MIN_H = 640

# =========================================================
# smartctl Helper (robust, mit absolutem Pfad & sudo -n)
# =========================================================

def _smartctl_candidates():
    return [
        os.environ.get("SMARTCTL") or "",  # Env-Override zuerst
        "smartctl",                        # PATH
        "/usr/sbin/smartctl",
        "/sbin/smartctl",
        "/usr/local/sbin/smartctl",
        "/usr/bin/smartctl",               # selten, aber möglich
    ]

def get_smartctl_path():
    for cand in _smartctl_candidates():
        if not cand:
            continue
        if os.path.basename(cand) == cand:
            p = shutil.which(cand)
            if p and os.access(p, os.X_OK):
                return p
        else:
            if os.path.exists(cand) and os.access(cand, os.X_OK):
                return cand
    return None

SMARTCTL = get_smartctl_path()

def have_smartctl():
    return SMARTCTL is not None

def run_cmd(cmd, timeout=30):
    try:
        p = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout, check=False, text=True
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "command not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"

def try_smartctl(args, timeout=30):
    """
    smartctl direkt über absoluten Pfad; bei Permission/Open-Problemen:
    sudo -n <ABSOLUTER_PFAD> …
    Liefert (rc, out, err, used_sudo: bool)
    """
    if SMARTCTL is None:
        return 127, "", "smartctl not found", False

    base = [SMARTCTL] + args
    rc, out, err = run_cmd(base, timeout=timeout)
    if rc == 0:
        return rc, out, err, False

    errtxt = (err or "") + "\n" + (out or "")
    perm_markers = (
        "Permission denied", "Open failed", "you must have root privileges",
        "Operation not permitted", "Device open failed"
    )
    if any(m in errtxt for m in perm_markers) or rc != 0:
        sudo = ["sudo", "-n", SMARTCTL] + args
        rc2, out2, err2 = run_cmd(sudo, timeout=timeout)
        return rc2, out2, err2, True

    return rc, out, err, False

def safe_json(out):
    try:
        return json.loads(out)
    except Exception:
        return None

def scan_devices():
    rc, out, err, used_sudo = try_smartctl(["--scan-open", "-j"], timeout=20)
    js = safe_json(out)
    if js is None:
        raise RuntimeError(f"smartctl scan fehlgeschlagen ({rc}).\n{err or out}")
    return js.get("devices", []), used_sudo

def fetch_device_json(devname, extra_args=None):
    """
    Holt JSON; gibt (js, used_sudo, rc) zurück.
    rc bevorzugt aus js['smartctl']['exit_status'].
    """
    args = ["-x", "-j"]
    if extra_args:
        args = extra_args + args
    rc, out, err, used_sudo = try_smartctl([devname] + args, timeout=40)
    js = safe_json(out)
    if js is None:
        raise RuntimeError(f"smartctl {devname} fehlgeschlagen ({rc}).\n{err or out}")
    tool_rc = js.get("smartctl", {}).get("exit_status")
    if isinstance(tool_rc, int):
        rc = tool_rc
    return js, used_sudo, rc

# =========================================================
# Auswerte-/Hilfsfunktionen
# =========================================================

def interpret_exit_status(mask):
    mapping = {
        1: "CLI-Fehler",
        2: "Gerät nicht öffnbar/Permission",
        4: "SMART Status FAIL",
        8: "Attribut FAILING_NOW",
        16: "Error-Log Fehler",
        32: "Self-Test-Log Fehler",
        64: "Gerätefehler gemeldet",
        128: "Weitere Fehler (Bit 128)",
    }
    return [txt for bit, txt in mapping.items() if mask & bit]

def get_health_summary(js):
    st = js.get("smart_status")
    if isinstance(st, dict) and "passed" in st:
        return bool(st["passed"]), ""
    return None, "SMART status unknown"

def get_model(js):
    for key in ("model_name", "device_model", "model_family", "vendor", "name"):
        v = js.get(key)
        if v:
            return v
    dev = js.get("device", {})
    for key in ("model_name", "name"):
        v = dev.get(key)
        if v:
            return v
    idinfo = js.get("identification", {})
    for key in ("model", "device"):
        v = idinfo.get(key)
        if v:
            return v
    return "Unknown model"

def get_serial(js):
    for key in ("serial_number", "serial", "nvme_serial_number"):
        v = js.get(key)
        if v:
            return v
    return "N/A"

def human_bytes(num_bytes):
    try:
        b = int(num_bytes)
    except Exception:
        return str(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if b < 1024 or unit == "PiB":
            return f"{b:.0f} {unit}"
        b //= 1024
    return f"{b} B"

def get_capacity(js):
    cap = js.get("user_capacity") or {}
    if isinstance(cap, dict):
        if "display" in cap:
            return cap["display"]
        if "bytes" in cap:
            return human_bytes(cap["bytes"])
    return "Unknown"

def get_temperature(js):
    temp = js.get("temperature")
    if isinstance(temp, dict) and "current" in temp:
        return f"{temp['current']} °C"
    nv = js.get("nvme_smart_health_information_log")
    if isinstance(nv, dict):
        for k in ("temperature", "composite_temperature"):
            if k in nv and isinstance(nv[k], (int, float)):
                return f"{nv[k]} °C"
    ata = js.get("ata_smart_attributes", {}).get("table", [])
    for row in ata:
        if row.get("id") in (194, 190):
            raw = row.get("raw", {})
            if "value" in raw and isinstance(raw["value"], int):
                return f"{raw['value']} °C"
            if "string" in raw:
                s = str(raw["string"])
                for token in s.split():
                    if token.isdigit():
                        return f"{token} °C"
                return s
    return "n/a"

def get_power_on_hours(js):
    pot = js.get("power_on_time")
    if isinstance(pot, dict):
        if "hours" in pot:
            return f"{pot['hours']} h"
        if "minutes" in pot:
            try:
                h = round(pot["minutes"]/60, 1)
                return f"{h} h"
            except Exception:
                return f"{pot['minutes']} min"
    ata = js.get("ata_smart_attributes", {}).get("table", [])
    for row in ata:
        if row.get("id") == 9:
            raw = row.get("raw", {})
            if "value" in raw and isinstance(raw["value"], int):
                return f"{raw['value']} h"
            if "string" in raw:
                return raw["string"]
    return "n/a"

def extract_ata_table(js):
    table = js.get("ata_smart_attributes", {}).get("table", [])
    rows = []
    for row in table:
        rows.append({
            "ID": row.get("id"),
            "Name": row.get("name", ""),
            "Value": row.get("value"),
            "Worst": row.get("worst"),
            "Thresh": row.get("thresh"),
            "WhenFailed": row.get("when_failed") or "",
            "Raw": (row.get("raw", {}).get("string")
                    or row.get("raw", {}).get("value")
                    or ""),
        })
    return rows

def extract_nvme_health(js):
    nv = js.get("nvme_smart_health_information_log", {})
    keys = [
        "temperature", "available_spare", "available_spare_threshold",
        "percentage_used", "data_units_read", "data_units_written",
        "host_read_commands", "host_write_commands", "controller_busy_time",
        "power_cycles", "power_on_hours", "unsafe_shutdowns",
        "media_errors", "num_err_log_entries"
    ]
    rows = []
    for k in keys:
        if k in nv:
            rows.append({"Key": k, "Value": nv[k]})
    return rows

def extract_selftest_log(js):
    st = js.get("ata_smart_self_test_log", {})
    std = st.get("standard", {})
    table = std.get("table", [])
    rows = []
    for r in table:
        rows.append({
            "Num": r.get("num"),
            "Type": r.get("type", ""),
            "Status": r.get("status", ""),
            "Segment": r.get("segment_number"),
            "LBA_first_error": r.get("lba_first_error"),
            "PowerOnHours": r.get("power_on_time", {}).get("hours"),
        })
    return rows

# ---------- Dateisystem: freier Speicher pro Laufwerk ----------

def list_mounts():
    paths = ["/proc/self/mounts", "/etc/mtab"]
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            mounts = []
            for ln in lines:
                parts = ln.split()
                if len(parts) >= 3:
                    src, mnt, fstype = parts[0], parts[1], parts[2]
                    mounts.append((src, mnt, fstype))
            return mounts
        except Exception:
            continue
    return []

def free_space_for_device(devname):
    """
    Summe des freien Platzes aller aktuell gemounteten Partitionen dieses Devices.
    Achtung: LVM/MD/LUKS-Mapper werden hier nicht dem physischen Device zugeordnet.
    """
    total_free = 0
    found = False
    for src, mnt, _ in list_mounts():
        try:
            if not src.startswith("/dev/"):
                continue
            if src == devname or src.startswith(devname):
                st = os.statvfs(mnt)
                free_bytes = st.f_bavail * st.f_frsize
                total_free += free_bytes
                found = True
        except Exception:
            pass
    if not found:
        return None
    return total_free

# =========================================================
# Self-Test Start (kompakt, deutsch, mit ETA)
# =========================================================

def start_selftest(devname, testtype="short"):
    rc, out, err, used_sudo = try_smartctl([devname, "-t", testtype], timeout=10)
    msg = (out or err or "").strip()

    eta_minutes = None
    eta_string = None

    m = re.search(r"Please wait\s+(\d+)\s+minutes?", msg, re.IGNORECASE)
    if m:
        try:
            eta_minutes = int(m.group(1))
        except Exception:
            pass

    m2 = re.search(r"will complete after\s+(.+)", msg, re.IGNORECASE)
    if m2:
        eta_string = m2.group(1).strip()

    if rc != 0 and not msg:
        raise RuntimeError("Selbsttest konnte nicht gestartet werden.")

    return {
        "text": msg,
        "eta_minutes": eta_minutes,
        "eta_string": eta_string,
    }

# =========================================================
# Tkinter App
# =========================================================

class SmartApp(Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(APP_MIN_W, APP_MIN_H)

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.devices = []     # Ergebnis --scan-open
        self.devinfo = {}     # Cache: devname -> (JSON, rc)

        self._build_ui()

        if not have_smartctl():
            messagebox.showerror(
                "smartctl fehlt",
                "smartctl wurde nicht gefunden.\n\n"
                "Tipps:\n"
                "• Installiere smartmontools (z. B. apt/pacman/dnf)\n"
                "• Prüfe den Pfad (häufig /usr/sbin/smartctl)\n"
                "• Alternativ: SMARTCTL=/usr/sbin/smartctl python3 smartgui.py"
            )
        else:
            self.refresh_devices_async()

    # ---------- UI Aufbau ----------

    def _build_ui(self):
        # Topbar
        topbar = ttk.Frame(self)
        topbar.pack(side=TOP, fill=X, padx=8, pady=6)

        ttk.Button(topbar, text="Neu scannen", command=self.refresh_devices_async).pack(side=LEFT)
        ttk.Button(topbar, text="Report speichern (JSON)", command=self.save_selected_report).pack(side=LEFT, padx=(8,0))

        self.sudo_label = ttk.Label(topbar, text="", foreground="#888888")
        self.sudo_label.pack(side=RIGHT)

        # Split: links Geräte / rechts Details
        main = ttk.Panedwindow(self, orient=HORIZONTAL)
        main.pack(fill=BOTH, expand=True, padx=8, pady=6)

        # Links: Geräte-Tabelle (mit neuer "Free"-Spalte)
        left = ttk.Frame(main)
        main.add(left, weight=1)

        columns = ("Device", "Type", "Model", "Serial", "Capacity", "Free", "Health", "Temp", "PowerOn")
        widths  = (160,      80,     220,     150,      120,        120,    90,       80,     90)
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=15)
        for c, w in zip(columns, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=W)
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_device)

        # Farben/Tags für Health
        self.tree.tag_configure("health_passed", foreground="#15803d")  # grün
        self.tree.tag_configure("health_failed", foreground="#b91c1c")  # rot
        self.tree.tag_configure("health_unknown", foreground="#b45309") # orange
        self.tree.tag_configure("health_err", foreground="#6b7280")     # grau

        # Rechts: Tabs
        right = ttk.Notebook(main)
        main.add(right, weight=2)

        # Übersicht
        self.tab_summary = ttk.Frame(right)
        right.add(self.tab_summary, text="Übersicht")
        self.summary_text = ttk.Treeview(self.tab_summary, columns=("Key", "Value"), show="headings")
        self.summary_text.heading("Key", text="Key")
        self.summary_text.heading("Value", text="Value")
        self.summary_text.column("Key", width=260, anchor=W)
        self.summary_text.column("Value", anchor=W)
        self.summary_text.pack(fill=BOTH, expand=True, padx=6, pady=6)

        # Attribute / Health
        self.tab_attr = ttk.Frame(right)
        right.add(self.tab_attr, text="Attribute / Health")
        self.attr_tree = ttk.Treeview(self.tab_attr, columns=("C1","C2","C3","C4","C5","C6","C7"), show="headings")
        headers = ("ID/Key","Name","Value","Worst","Thresh","WhenFailed","Raw/Value")
        widths2 = (70, 180, 80, 80, 80, 120, 240)
        for i, (name, w) in enumerate(zip(headers, widths2), start=1):
            cid = f"C{i}"
            self.attr_tree.heading(cid, text=name)
            self.attr_tree.column(cid, width=w, anchor=W)
        self.attr_tree.pack(fill=BOTH, expand=True, padx=6, pady=(6,0))

        # Selbsttests
        self.tab_tests = ttk.Frame(right)
        right.add(self.tab_tests, text="Selbsttests")

        test_bar = ttk.Frame(self.tab_tests)
        test_bar.pack(side=TOP, fill=X, padx=6, pady=6)

        ttk.Button(test_bar, text="Kurztest starten", command=lambda: self.start_test_async("short")).pack(side=LEFT)
        ttk.Button(test_bar, text="Langtest starten", command=lambda: self.start_test_async("long")).pack(side=LEFT, padx=(6,0))
        ttk.Button(test_bar, text="Test-Log neu laden", command=self.load_selftests_async).pack(side=LEFT, padx=(12,0))

        self.tests_tree = ttk.Treeview(self.tab_tests, columns=("Num","Type","Status","Segment","LBA_first_error","PowerOnHours"), show="headings")
        for col, w in zip(("Num","Type","Status","Segment","LBA_first_error","PowerOnHours"), (60,120,260,100,150,120)):
            self.tests_tree.heading(col, text=col)
            self.tests_tree.column(col, width=w, anchor=W)
        self.tests_tree.pack(fill=BOTH, expand=True, padx=6, pady=(0,6))

        # Statusbar
        self.status_var = ttk.Label(self, text="Bereit", anchor=W)
        self.status_var.pack(side=BOTTOM, fill=X)

    # ---------- Async Helper ----------

    def set_busy(self, busy=True, note=""):
        self.config(cursor="watch" if busy else "")
        self.status_var.config(text=note if note else ("Arbeite..." if busy else "Bereit"))
        self.update_idletasks()

    def bg(self, func, done=None, note=""):
        q = queue.Queue()

        def worker():
            try:
                res = func()
                q.put(("ok", res))
            except Exception as e:
                q.put(("err", e))

        def poll():
            try:
                kind, payload = q.get_nowait()
            except queue.Empty:
                self.after(100, poll)
                return
            self.set_busy(False)
            if kind == "ok":
                if done:
                    done(payload)
            else:
                messagebox.showerror("Fehler", str(payload))

        self.set_busy(True, note)
        threading.Thread(target=worker, daemon=True).start()
        self.after(100, poll)

    # ---------- Health/Color ----------

    def _health_tag_for(self, passed, rc):
        if passed is False:
            return "health_failed"
        if passed is True:
            return "health_passed" if (rc == 0 or rc is None) else "health_unknown"
        return "health_unknown"

    # ---------- Aktionen ----------

    def refresh_devices_async(self):
        def work():
            devs, used_sudo = scan_devices()
            return (devs, used_sudo)

        def done(result):
            devs, used_sudo = result
            if used_sudo:
                self.sudo_label.config(text="Zugriff via sudo")
            self.devices = devs
            self.populate_device_list()

        if not have_smartctl():
            messagebox.showerror("smartctl fehlt", "smartctl wurde nicht gefunden. Siehe Hinweis beim Start.")
            return

        self.bg(work, done, note="Scanne Geräte…")

    def _free_space_string(self, devname):
        free = free_space_for_device(devname)
        if free is None:
            return "n/a"
        return human_bytes(free)

    def populate_device_list(self):
        self.tree.delete(*self.tree.get_children())
        self.devinfo.clear()

        for d in self.devices:
            devname = d.get("name") or d.get("info_name") or d.get("dev_name")
            dtype = d.get("type", "disk")
            model = serial = capacity = free_str = health = temp = poh = ""
            tag = "health_err"  # default
            try:
                js, _, rc = fetch_device_json(devname)
                self.devinfo[devname] = (js, rc)
                model = get_model(js)
                serial = get_serial(js)
                capacity = get_capacity(js)
                free_str = self._free_space_string(devname)
                passed, _ = get_health_summary(js)
                health = "PASSED" if passed is True else ("FAILED" if passed is False else "UNKNOWN")
                temp = get_temperature(js)
                poh = get_power_on_hours(js)
                tag = self._health_tag_for(passed, rc)
            except Exception:
                model = "(keine Daten)"
                health = "ERR"
                temp = "n/a"
                poh = "n/a"
                free_str = "n/a"
                tag = "health_err"

            self.tree.insert(
                "", END, iid=devname,
                values=(devname, dtype, model, serial, capacity, free_str, health, temp, poh),
                tags=(tag,)
            )

        kids = self.tree.get_children()
        if kids:
            self.tree.selection_set(kids[0])
            self.on_select_device()

    def on_select_device(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        devname = sel[0]

        def work():
            js, _, rc = fetch_device_json(devname)
            self.devinfo[devname] = (js, rc)
            return (js, rc)

        def done(payload):
            js, rc = payload
            self.fill_summary(js, devname, rc)
            self.fill_attributes(js)
            self.fill_selftests(js)

        self.bg(work, done, note=f"Lese {devname}…")

    def fill_summary(self, js, devname, rc=0):
        self.summary_text.delete(*self.summary_text.get_children())
        kv = [
            ("Gerät", devname),
            ("Modell", get_model(js)),
            ("Seriennummer", get_serial(js)),
            ("Kapazität", get_capacity(js)),
            ("Freier Speicher (gemountet)", self._free_space_string(devname)),
        ]
        passed, _ = get_health_summary(js)
        kv.append(("SMART Health", "PASSED" if passed is True else ("FAILED" if passed is False else "UNKNOWN")))
        kv.append(("Temperatur", get_temperature(js)))
        kv.append(("Power-On-Time", get_power_on_hours(js)))

        if isinstance(rc, int) and rc != 0:
            bits = ", ".join(interpret_exit_status(rc)) or f"Code {rc}"
            kv.append(("smartctl Exit-Status", f"{rc} ({bits})"))

        fw = js.get("firmware_version") or js.get("firmware") or js.get("device", {}).get("firmware")
        if fw:
            kv.append(("Firmware", fw))
        xport = js.get("device", {}).get("protocol")
        if xport:
            kv.append(("Protokoll", xport))
        rr = js.get("rotation_rate")
        if rr:
            kv.append(("Rotation", f"{rr} rpm" if isinstance(rr, int) else str(rr)))

        for k, v in kv:
            self.summary_text.insert("", END, values=(k, v))

    def fill_attributes(self, js):
        self.attr_tree.delete(*self.attr_tree.get_children())
        ata_rows = extract_ata_table(js)
        if ata_rows:
            for r in ata_rows:
                self.attr_tree.insert("", END, values=(
                    r["ID"], r["Name"], r["Value"], r["Worst"], r["Thresh"], r["WhenFailed"], r["Raw"]
                ))
        else:
            nv_rows = extract_nvme_health(js)
            if nv_rows:
                for r in nv_rows:
                    self.attr_tree.insert("", END, values=(r["Key"], "", "", "", "", "", r["Value"]))
            else:
                self.attr_tree.insert("", END, values=("", "Keine Attribute verfügbar", "", "", "", "", ""))

    def fill_selftests(self, js):
        self.tests_tree.delete(*self.tests_tree.get_children())
        rows = extract_selftest_log(js)
        if rows:
            for r in rows:
                self.tests_tree.insert("", END, values=(
                    r["Num"], r["Type"], r["Status"], r["Segment"], r["LBA_first_error"], r["PowerOnHours"]
                ))
        else:
            self.tests_tree.insert("", END, values=("—", "—", "(Kein Self-Test-Log verfügbar)", "—", "—", "—"))

    def selected_device(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    # ---- Self-Test starten (kompakter Dialog + Auto-Reload) ----

    def start_test_async(self, kind="short"):
        dev = self.selected_device()
        if not dev:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Laufwerk auswählen.")
            return

        def work():
            return start_selftest(dev, kind)

        def done(info):
            eta_lines = []
            if info.get("eta_minutes") is not None:
                eta_lines.append(f"Geschätzte Dauer: ~{info['eta_minutes']} Minute(n)")
            if info.get("eta_string"):
                eta_lines.append(f"Voraussichtlich fertig: {info['eta_string']}")

            body = [f"{kind.capitalize()}-Test auf {dev} gestartet."]
            if eta_lines:
                body.append("")
                body.extend(eta_lines)
            body.append("")
            body.append("Der Test läuft im Hintergrund. Du kannst das Fenster schließen.")
            messagebox.showinfo("Selbsttest", "\n".join(body))

            # Auto-Reload Selftest-Log
            minutes = info.get("eta_minutes")
            if isinstance(minutes, int) and minutes > 0:
                delay_ms = (minutes * 60 + 10) * 1000  # +10s Puffer
                self.after(delay_ms, self.load_selftests_async)
            else:
                # Fallback (2 min kurz, ~75 min lang)
                fallback_min = 2 if kind == "short" else 75
                self.after(fallback_min * 60 * 1000, self.load_selftests_async)

        self.bg(work, done, note=f"Starte {kind}-Test auf {dev}…")

    def load_selftests_async(self):
        dev = self.selected_device()
        if not dev:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Laufwerk auswählen.")
            return

        def work():
            js, _, rc = fetch_device_json(dev)
            self.devinfo[dev] = (js, rc)
            return js

        def done(js):
            self.fill_selftests(js)

        self.bg(work, done, note=f"Lese Test-Log von {dev}…")

    def save_selected_report(self):
        dev = self.selected_device()
        if not dev:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Laufwerk auswählen.")
            return
        entry = self.devinfo.get(dev)
        if not entry:
            messagebox.showerror("Fehler", "Keine Gerätedaten im Cache. Bitte neu laden.")
            return
        js, rc = entry
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default = f"smart_report_{os.path.basename(dev).replace('/','_')}_{ts}.json"
        path = filedialog.asksaveasfilename(
            title="Report speichern",
            defaultextension=".json",
            initialfile=default,
            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(js, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Gespeichert", f"Report gespeichert:\n{path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Report nicht speichern:\n{e}")

# =========================================================
# main
# =========================================================

def main():
    app = SmartApp()
    app.mainloop()

if __name__ == "__main__":
    main()
