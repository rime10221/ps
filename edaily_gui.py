# -*- coding: utf-8 -*-
"""
E-daily 입원(step=2) 자동화 GUI
- 디버깅 포트(9222)로 띄운 크롬에 attach
- ① 입원목록.xls -> 전체 환자 기본정보 폼 입력
- ② 화면에서 대상 환자 1명 선택 + 진단명 텍스트 붙여넣기 -> 진단코드 입력
저장은 사용자가 브라우저에서 직접 확인 후 누름.
"""
import os
import sys
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import edaily_core as core

# exe(PyInstaller onefile)로 실행 시엔 exe가 있는 폴더, 스크립트 실행 시엔 소스 폴더
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_XLS = os.path.join(BASE_DIR, "입원목록.xls")
DEFAULT_ER = os.path.join(BASE_DIR, "ER.xls")
DEBUG_PORT = 9222


class App:
    def __init__(self, root):
        self.root = root
        root.title("E-daily 입원 자동화")
        root.geometry("720x780")

        self.driver = None
        self.patients = []          # xls 파싱 결과
        self.log_q = queue.Queue()

        pad = {"padx": 8, "pady": 4}

        # ── ⓪ 크롬 실행 ─────────────────────────────
        f0 = ttk.LabelFrame(root, text="⓪ 크롬 (디버깅 모드)")
        f0.pack(fill="x", **pad)
        ttk.Button(f0, text="크롬 디버깅 모드로 열기 (E-daily 접속)",
                   command=self.do_launch_chrome).pack(fill="x", padx=6, pady=6)
        ttk.Label(f0, text="→ 열린 크롬에서 로그인 후, 작성할 페이지(02/03)를 띄워두세요.",
                  foreground="#555").pack(anchor="w", padx=8, pady=(0, 4))

        # ── ① 기본정보 ──────────────────────────────
        f1 = ttk.LabelFrame(root, text="① 기본정보 (입원목록.xls → 폼)")
        f1.pack(fill="x", **pad)

        row = ttk.Frame(f1); row.pack(fill="x", padx=6, pady=4)
        ttk.Label(row, text="xls 경로:").pack(side="left")
        self.xls_var = tk.StringVar(value=DEFAULT_XLS if os.path.exists(DEFAULT_XLS) else "")
        ttk.Entry(row, textvariable=self.xls_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row, text="찾아보기", command=self.browse_xls).pack(side="left")

        self.btn_basic = ttk.Button(f1, text="환자 불러오기 & 기본정보 폼 채우기",
                                    command=lambda: self.run_bg(self.do_basic))
        self.btn_basic.pack(fill="x", padx=6, pady=6)

        # ── ② 진단명 ────────────────────────────────
        f2 = ttk.LabelFrame(root, text="② 진단명 (화면에서 대상 환자 1명 선택)")
        f2.pack(fill="both", expand=False, **pad)

        row2 = ttk.Frame(f2); row2.pack(fill="x", padx=6, pady=4)
        ttk.Label(row2, text="대상 환자:").pack(side="left")
        self.patient_var = tk.StringVar()
        self.patient_cb = ttk.Combobox(row2, textvariable=self.patient_var, state="readonly")
        self.patient_cb.pack(side="left", fill="x", expand=True, padx=4)

        ttk.Label(f2, text="진단명 붙여넣기 (진단명.txt 형식, 탭 구분):").pack(anchor="w", padx=6)
        self.dx_text = tk.Text(f2, height=8, wrap="none")
        self.dx_text.pack(fill="both", expand=True, padx=6, pady=4)

        self.btn_dx = ttk.Button(f2, text="선택 환자에 진단명 입력",
                                 command=lambda: self.run_bg(self.do_diagnosis))
        self.btn_dx.pack(fill="x", padx=6, pady=6)

        # ── ③ EMERGENCY ROOM ────────────────────────
        f_er = ttk.LabelFrame(root, text="③ EMERGENCY ROOM (ER.xls → 03 페이지, 병실 ER·전원 퇴원 고정)")
        f_er.pack(fill="x", **pad)
        rowe = ttk.Frame(f_er); rowe.pack(fill="x", padx=6, pady=4)
        ttk.Label(rowe, text="ER.xls 경로:").pack(side="left")
        self.er_var = tk.StringVar(value=DEFAULT_ER if os.path.exists(DEFAULT_ER) else "")
        ttk.Entry(rowe, textvariable=self.er_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(rowe, text="찾아보기", command=self.browse_er).pack(side="left")
        self.btn_er = ttk.Button(f_er, text="응급실(EMERGENCY ROOM) 환자 채우기",
                                 command=lambda: self.run_bg(self.do_er))
        self.btn_er.pack(fill="x", padx=6, pady=6)

        # ── 로그 ────────────────────────────────────
        f3 = ttk.LabelFrame(root, text="로그")
        f3.pack(fill="both", expand=True, **pad)
        self.log_text = tk.Text(f3, height=10, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=4)

        self.root.after(100, self._drain_log)

    # ── 로그/스레드 유틸 ──────────────────────────────
    def log(self, msg):
        self.log_q.put(str(msg))

    def _drain_log(self):
        while not self.log_q.empty():
            msg = self.log_q.get()
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.root.after(100, self._drain_log)

    def run_bg(self, fn):
        """버튼 핸들러: 백그라운드 스레드 실행 + 버튼 잠금"""
        self._set_buttons("disabled")

        def wrap():
            try:
                fn()
            except Exception as e:
                self.log(f"[오류] {e}")
                messagebox.showerror("오류", str(e))
            finally:
                self.root.after(0, lambda: self._set_buttons("normal"))
        threading.Thread(target=wrap, daemon=True).start()

    def _set_buttons(self, state):
        self.btn_basic.config(state=state)
        self.btn_dx.config(state=state)
        self.btn_er.config(state=state)

    # ── 크롬 연결 ────────────────────────────────────
    def ensure_driver(self):
        """크롬 연결만 보장 (탭 전환은 각 동작이 switch_to_step 으로 수행)."""
        if self.driver is not None:
            try:
                _ = self.driver.window_handles  # 살아있는지 확인
                return self.driver
            except Exception:
                self.driver = None
        self.log(f"크롬(127.0.0.1:{DEBUG_PORT}) 연결 중...")
        self.driver = core.attach_chrome(DEBUG_PORT)
        self.log("연결 완료.")
        return self.driver

    # ER 도 동일 드라이버 사용 (fill_emergency_room 내부에서 step=3 전환)
    ensure_driver_step3 = ensure_driver

    # ── 동작 ────────────────────────────────────────
    def do_launch_chrome(self):
        try:
            path = core.launch_debug_chrome()
            self.log(f"크롬 실행: {path}")
            self.log(f"→ {core.BASE_URL} (디버깅 포트 {DEBUG_PORT})")
        except Exception as e:
            self.log(f"[오류] {e}")
            messagebox.showerror("오류", str(e))

    def browse_xls(self):
        p = filedialog.askopenfilename(
            title="입원목록.xls 선택",
            filetypes=[("Excel 97-2003", "*.xls"), ("모든 파일", "*.*")])
        if p:
            self.xls_var.set(p)

    def do_basic(self):
        path = self.xls_var.get().strip()
        if not path or not os.path.exists(path):
            raise FileNotFoundError("입원목록.xls 경로를 확인하세요.")
        self.log(f"xls 읽는 중: {path}")
        self.patients = core.parse_admission_xls(path)
        self.log(f"환자 {len(self.patients)}명 파싱됨.")

        # 대상환자 드롭다운 갱신
        items = [f"{i}. {p['regnum']} {p['name']} ({p['sex']}/{p['age']})"
                 for i, p in enumerate(self.patients, start=1)]
        self.root.after(0, lambda: self._set_patients(items))

        d = self.ensure_driver()
        core.fill_basic_info(d, self.patients, log=self.log)

    def _set_patients(self, items):
        self.patient_cb["values"] = items
        if items:
            self.patient_cb.current(0)

    def do_diagnosis(self):
        if not self.patients:
            raise RuntimeError("먼저 ①에서 환자를 불러오세요.")
        sel = self.patient_cb.current()
        if sel < 0:
            raise RuntimeError("대상 환자를 선택하세요.")
        row_index = sel + 1  # admission_{row_index}

        text = self.dx_text.get("1.0", "end")
        diags = core.parse_diagnosis_text(text)
        if not diags:
            raise RuntimeError("진단명 텍스트가 비었거나 형식이 맞지 않습니다.")

        p = self.patients[sel]
        self.log(f"[{row_index}행] {p['regnum']} {p['name']} 에 진단 {len(diags)}건 입력...")
        d = self.ensure_driver()
        core.fill_diagnosis(d, row_index, diags,
                            insurance=p["insurance"], doctor=p["doctor"], log=self.log)

    def browse_er(self):
        p = filedialog.askopenfilename(
            title="ER.xls 선택",
            filetypes=[("Excel 97-2003", "*.xls"), ("모든 파일", "*.*")])
        if p:
            self.er_var.set(p)

    def do_er(self):
        path = self.er_var.get().strip()
        if not path or not os.path.exists(path):
            raise FileNotFoundError("ER.xls 경로를 확인하세요.")
        self.log(f"ER.xls 읽는 중: {path}")
        er_patients = core.parse_er_xls(path)
        self.log(f"응급실 환자 {len(er_patients)}명 파싱됨.")
        d = self.ensure_driver_step3()
        core.fill_emergency_room(d, er_patients, log=self.log)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
