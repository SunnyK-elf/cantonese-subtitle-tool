#!/usr/bin/env python3
"""粤语字幕工具 —— 图形界面版。

运行：
    python gui.py

首次使用：点「密钥设置」填入阿里云百炼 + 豆包/GPT 的 Key（保存后下次免填）。
"""
import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from cantonese_tool import audio, pipeline


def _app_dir() -> Path:
    """返回配置存放目录：打包成 exe 时为 exe 所在目录，源码运行时为脚本目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()
CONFIG_FILE = APP_DIR / "config.json"

DEFAULTS = {
    "dashscope_key": "",
    "ark_key": "",
    "openai_key": "",
    "provider": "doubao",
    "asr_engine": "cloud",
    "custom_base_url": "",
    "custom_model": "",
    "custom_key": "",
    "font": "Microsoft YaHei",
    "font_size": 24,
    "output_dir": "output",
}


def load_settings() -> dict:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return {**DEFAULTS, **data}
        except Exception:
            pass
    return dict(DEFAULTS)


def save_settings(s: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.settings = load_settings()
        self.q = queue.Queue()
        self.running = False
        self.last_output_dir = None
        self._build_ui()
        self._check_ffmpeg()
        root.after(100, self._poll_queue)

    # ---------- UI 构建 ----------
    def _build_ui(self):
        self.root.title("粤语字幕工具 · 识别 + 翻译 + 烧录")
        self.root.geometry("720x560")
        self.root.minsize(680, 520)

        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        # 标题
        ttk.Label(frm, text="粤语视频字幕工具", font=("Microsoft YaHei", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )

        # 输入文件
        ttk.Label(frm, text="① 输入文件").grid(row=1, column=0, sticky="w", **pad)
        self.input_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.input_var).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="选择文件", command=self._pick_input).grid(row=1, column=2, **pad)

        # 输出目录
        ttk.Label(frm, text="② 输出目录").grid(row=2, column=0, sticky="w", **pad)
        self.outdir_var = tk.StringVar(value=self.settings.get("output_dir", "output"))
        ttk.Entry(frm, textvariable=self.outdir_var).grid(row=2, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="选择目录", command=self._pick_outdir).grid(row=2, column=2, **pad)

        # 选项
        opts = ttk.LabelFrame(frm, text="③ 选项", padding=10)
        opts.grid(row=3, column=0, columnspan=3, sticky="ew", padx=12, pady=8)
        opts.columnconfigure(1, weight=1)

        # 翻译
        self.provider_var = tk.StringVar(value=self.settings.get("provider", "doubao"))
        ttk.Label(opts, text="翻译").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(opts, text="豆包", variable=self.provider_var, value="doubao",
                        command=self._refresh_key_status).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(opts, text="GPT", variable=self.provider_var, value="openai",
                        command=self._refresh_key_status).grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(opts, text="自定义", variable=self.provider_var, value="custom",
                        command=self._refresh_key_status).grid(row=0, column=3, sticky="w")

        self.mandarin_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="只烧普通话（默认双语：粤语+普通话）", variable=self.mandarin_var).grid(
            row=1, column=0, columnspan=4, sticky="w"
        )

        # 字体字号
        ttk.Label(opts, text="字体").grid(row=2, column=0, sticky="w", pady=6)
        self.font_var = tk.StringVar(value=self.settings.get("font", "Microsoft YaHei"))
        ttk.Entry(opts, textvariable=self.font_var, width=18).grid(row=2, column=1, sticky="w", pady=6)
        ttk.Label(opts, text="字号").grid(row=2, column=2, sticky="w", pady=6)
        self.size_var = tk.IntVar(value=self.settings.get("font_size", 24))
        ttk.Spinbox(opts, from_=16, to=60, textvariable=self.size_var, width=6).grid(row=2, column=3, sticky="w", pady=6)

        # 识别引擎
        self.asr_engine_var = tk.StringVar(value=self.settings.get("asr_engine", "cloud"))
        ttk.Label(opts, text="识别").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Radiobutton(opts, text="云端（阿里云）", variable=self.asr_engine_var, value="cloud",
                        command=self._refresh_key_status).grid(row=3, column=1, sticky="w", pady=(6, 0))
        ttk.Radiobutton(opts, text="本地（免费，免 key）", variable=self.asr_engine_var, value="local",
                        command=self._refresh_key_status).grid(row=3, column=2, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Label(opts, foreground="#888",
                  text="本地识别首次使用会自动下载模型到本工具 models/ 目录（约 1.5GB，不写 C 盘）").grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(0, 2))

        # 自定义翻译（选「自定义」时生效）：接口 | 模型 | key
        self.custom_base_url_var = tk.StringVar(value=self.settings.get("custom_base_url", ""))
        self.custom_model_var = tk.StringVar(value=self.settings.get("custom_model", ""))
        self.custom_key_var = tk.StringVar(value=self.settings.get("custom_key", ""))
        ttk.Label(opts, text="自定义").grid(row=5, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(opts, textvariable=self.custom_base_url_var).grid(row=5, column=1, sticky="ew", pady=(6, 0))
        ttk.Entry(opts, textvariable=self.custom_model_var, width=16).grid(row=5, column=2, sticky="w", padx=4, pady=(6, 0))
        ttk.Entry(opts, textvariable=self.custom_key_var, width=16).grid(row=5, column=3, sticky="w", pady=(6, 0))
        ttk.Label(opts, foreground="#888",
                  text="上面三格依次是「接口地址 / 模型名 / key」。本地 ollama 免费翻译：接口 http://localhost:11434/v1，模型 qwen2.5:7b，key 留空即可").grid(
            row=6, column=0, columnspan=4, sticky="w", pady=(0, 2))

        # 密钥
        keys = ttk.LabelFrame(frm, text="④ 密钥", padding=10)
        keys.grid(row=4, column=0, columnspan=3, sticky="ew", padx=12, pady=8)
        keys.columnconfigure(1, weight=1)
        self.key_status_var = tk.StringVar()
        ttk.Label(keys, textvariable=self.key_status_var).grid(row=0, column=0, sticky="w")
        ttk.Button(keys, text="密钥设置", command=self._open_key_dialog).grid(row=0, column=1, sticky="e")
        self._refresh_key_status()

        # 开始按钮
        self.start_btn = ttk.Button(frm, text="开始处理", command=self._start)
        self.start_btn.grid(row=5, column=0, columnspan=3, sticky="ew", padx=12, pady=(8, 4))

        # 进度条
        self.progress = ttk.Progressbar(frm, mode="indeterminate")
        self.progress.grid(row=6, column=0, columnspan=3, sticky="ew", padx=12, pady=4)

        # 日志
        logfrm = ttk.LabelFrame(frm, text="进度日志", padding=6)
        logfrm.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=12, pady=4)
        frm.rowconfigure(7, weight=1)
        self.log_text = tk.Text(logfrm, height=10, wrap="word", state="disabled",
                                font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)

        self.open_btn = ttk.Button(frm, text="打开输出文件夹", command=self._open_output, state="disabled")
        self.open_btn.grid(row=8, column=0, columnspan=3, sticky="ew", padx=12, pady=(4, 0))

    # ---------- 交互 ----------
    def _pick_input(self):
        f = filedialog.askopenfilename(
            title="选择视频或音频文件",
            filetypes=[
                ("视频/音频", "*.mp4 *.mkv *.mov *.avi *.flv *.webm *.m4v *.ts *.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus"),
                ("所有文件", "*.*"),
            ],
        )
        if f:
            self.input_var.set(f)

    def _pick_outdir(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.outdir_var.set(d)

    def _refresh_key_status(self):
        prov = self.provider_var.get()
        engine = self.asr_engine_var.get()
        has_asr = bool(self.settings.get("dashscope_key")) or engine == "local"
        if prov == "doubao":
            has_trans = bool(self.settings.get("ark_key"))
        elif prov == "openai":
            has_trans = bool(self.settings.get("openai_key"))
        else:  # custom
            has_trans = bool(self.custom_base_url_var.get().strip()) and bool(self.custom_model_var.get().strip())
        if has_asr and has_trans:
            self.key_status_var.set("✅ 密钥已配置")
        elif has_asr or has_trans:
            self.key_status_var.set("⚠️ 还缺翻译配置（豆包/GPT 密钥，或自定义接口地址+模型）")
        else:
            self.key_status_var.set("⚠️ 未配置密钥 —— 点右侧「密钥设置」填写")

    def _open_key_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("密钥设置")
        dlg.geometry("560x240")
        dlg.resizable(False, False)
        dlg.grab_set()

        rows = [
            ("阿里云百炼（粤语识别）", "dashscope_key"),
            ("火山方舟豆包（翻译）", "ark_key"),
            ("OpenAI（翻译，可选）", "openai_key"),
        ]
        vars_ = {}
        for i, (label, key) in enumerate(rows):
            ttk.Label(dlg, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=8)
            v = tk.StringVar(value=self.settings.get(key, ""))
            vars_[key] = v
            ttk.Entry(dlg, textvariable=v, width=44, show="*").grid(row=i, column=1, sticky="w", padx=6, pady=8)

        hint = ttk.Label(dlg, foreground="#888",
                         text="密钥保存在本工具目录的 config.json 中，不会上传。\n"
                              "获取：阿里云百炼 bailian.console.aliyun.com ；火山方舟 console.volcengine.com/ark")
        hint.grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=6)

        def _save():
            for k, v in vars_.items():
                self.settings[k] = v.get().strip()
            save_settings(self.settings)
            self._refresh_key_status()
            dlg.destroy()
            messagebox.showinfo("已保存", "密钥已保存。")

        ttk.Button(dlg, text="保存", command=_save).grid(row=4, column=0, columnspan=2, pady=10)

    def _check_ffmpeg(self):
        try:
            audio.find_ffmpeg()
        except Exception as e:
            self._append_log("⚠️ " + str(e))
            messagebox.showwarning("缺少 ffmpeg", str(e))

    def _append_log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ---------- 执行 ----------
    def _start(self):
        if self.running:
            return
        src = self.input_var.get().strip()
        if not src:
            messagebox.showwarning("提示", "请先选择输入视频/音频文件。")
            return
        provider = self.provider_var.get()
        engine = self.asr_engine_var.get()
        custom_base_url = self.custom_base_url_var.get().strip()
        custom_model = self.custom_model_var.get().strip()
        custom_key = self.custom_key_var.get().strip()
        keys = {
            "dashscope": self.settings.get("dashscope_key", ""),
            "ark": self.settings.get("ark_key", ""),
            "openai": self.settings.get("openai_key", ""),
        }
        if engine == "cloud" and not keys["dashscope"]:
            messagebox.showwarning("提示", "当前是云端识别，缺少阿里云百炼密钥。可在「密钥设置」填写，或切换到「本地」识别。")
            return
        if provider == "doubao" and not keys["ark"]:
            messagebox.showwarning("提示", "缺少豆包密钥（用于翻译），请先到「密钥设置」填写。")
            return
        if provider == "openai" and not keys["openai"]:
            messagebox.showwarning("提示", "缺少 OpenAI 密钥（用于翻译），请先到「密钥设置」填写。")
            return
        if provider == "custom" and (not custom_base_url or not custom_model):
            messagebox.showwarning("提示", "自定义翻译需填写「接口地址」和「模型名」。")
            return

        outdir = self.outdir_var.get().strip() or "output"
        self.last_output_dir = Path(outdir).resolve()

        self.settings.update(
            provider=provider,
            asr_engine=engine,
            custom_base_url=custom_base_url,
            custom_model=custom_model,
            custom_key=custom_key,
            font=self.font_var.get().strip() or "Microsoft YaHei",
            font_size=int(self.size_var.get()),
            output_dir=outdir,
        )
        save_settings(self.settings)

        self._append_log(f"开始处理：{src}")
        self.running = True
        self.start_btn.configure(state="disabled")
        self.progress.start(12)

        t = threading.Thread(
            target=self._worker,
            args=(src, outdir, provider, engine, custom_base_url, custom_model, custom_key, keys),
            daemon=True,
        )
        t.start()

    def _worker(self, src, outdir, provider, engine, custom_base_url, custom_model, custom_key, keys):
        try:
            outputs = pipeline.run(
                input_path=src,
                output_dir=outdir,
                provider=provider,
                mandarin_only=self.mandarin_var.get(),
                font=self.font_var.get().strip() or "Microsoft YaHei",
                font_size=int(self.size_var.get()),
                asr_engine=engine,
                model_dir=str(APP_DIR / "models"),
                model_size="medium",
                model=custom_model if provider == "custom" else None,
                dashscope_key=keys["dashscope"],
                ark_key=keys["ark"],
                openai_key=keys["openai"],
                custom_base_url=custom_base_url,
                custom_key=custom_key,
                log=lambda m: self.q.put(("log", m)),
            )
            self.q.put(("done", outputs))
        except Exception as e:  # noqa: BLE001
            self.q.put(("error", str(e)))

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "done":
                    self._finish(payload)
                elif kind == "error":
                    self._fail(payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _finish(self, outputs):
        self.running = False
        self.progress.stop()
        self.start_btn.configure(state="normal")
        self.open_btn.configure(state="normal")
        self._append_log("✅ 处理完成！输出文件：")
        for o in outputs:
            self._append_log("   " + str(o))
        if messagebox.askyesno("完成", "处理完成，是否打开输出文件夹？"):
            self._open_output()

    def _fail(self, err):
        self.running = False
        self.progress.stop()
        self.start_btn.configure(state="normal")
        self._append_log("❌ 处理失败：" + err)
        messagebox.showerror("处理失败", err)

    def _open_output(self):
        d = self.last_output_dir or Path(self.outdir_var.get() or "output").resolve()
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(d))  # type: ignore[attr-defined]
        elif sys_platform() == "darwin":
            subprocess.Popen(["open", str(d)])
        else:
            subprocess.Popen(["xdg-open", str(d)])


def sys_platform():
    import sys
    return sys.platform


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
