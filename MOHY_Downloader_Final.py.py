# -- coding: utf-8 --

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import os
import sys
import re
import json

# --- الإعدادات والمكتبات ---
try:
    import yt_dlp
except ImportError:
    messagebox.showerror("خطأ في المكتبات", "يرجى تثبيت المكتبات المطلوبة:\n pip install yt-dlp")
    sys.exit(1)

CONFIG_FILE = "mohy_downloader_config.json"
LANG_FILE = "languages.json"

# --- الفئة الرئيسية للتطبيق ---
class MohyDownloaderApp:
    def __init__(self, master):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._load_languages()
        self.video_duration = 0; self.after_id = None; self.ffmpeg_process = None
        self.last_save_dir = tk.StringVar(); self.last_download_path = ""; self.repeat_job = None
        self.url_var = tk.StringVar(); self.filename_var = tk.StringVar()
        self.quality_var = tk.StringVar(value='720p')
        self.status_var = tk.StringVar()
        self.cookie_file_var = tk.StringVar(); self.video_duration_str_var = tk.StringVar()
        self.start_time_str_var = tk.StringVar(value="00:00:00"); self.end_time_str_var = tk.StringVar(value="00:00:00")
        self.high_accuracy_var = tk.BooleanVar(value=False)
        self._create_widgets()
        self._check_ffmpeg()
        self._load_config()
        self._reset_ui_for_new_url()
   
    def _load_languages(self):
        try:
            # هذه الدالة السحرية تجد المسار الصحيح سواء في وضع التطوير أو كملف exe
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            lang_path = os.path.join(base_path, LANG_FILE)
            with open(lang_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            messagebox.showerror("Error", "Language file 'languages.json' is missing or corrupted.")
            sys.exit(1)
        self.current_lang = tk.StringVar(value="ar")
    
    def _t(self, key, **kwargs):
        return self.translations.get(self.current_lang.get(), {}).get(key, key).format(**kwargs)

    def _create_widgets(self):
        self.master.geometry("600x600"); self.master.resizable(False, False)
        main_frame = ttk.Frame(self.master, padding="15"); main_frame.pack(fill=tk.BOTH, expand=True)
        lang_frame = ttk.Frame(main_frame); lang_frame.grid(row=0, column=1, sticky='e', pady=(0,10))
        ttk.Label(lang_frame, text="Language:").pack(side=tk.LEFT)
        self.lang_menu = ttk.Combobox(lang_frame, textvariable=self.current_lang, values=list(self.translations.keys()), state="readonly", width=5)
        self.lang_menu.pack(side=tk.LEFT); self.lang_menu.bind("<<ComboboxSelected>>", self._change_language)
        self.paste_url_label = ttk.Label(main_frame, font=('Segoe UI', 10, 'bold')); self.paste_url_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        url_frame = ttk.Frame(main_frame); url_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var); self.url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=4); self.url_entry.bind("<KeyRelease>", self._on_url_change)
        self.paste_button = ttk.Button(url_frame, width=8, command=self._paste_from_clipboard); self.paste_button.pack(side=tk.LEFT, padx=(5, 0))
        self.select_clip_label = ttk.Label(main_frame, font=('Segoe UI', 10, 'bold')); self.select_clip_label.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(15, 5))
        self.duration_label = ttk.Label(main_frame, textvariable=self.video_duration_str_var, anchor="center"); self.duration_label.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.start_frame = ttk.Frame(main_frame); self.start_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5,0))
        self.end_frame = ttk.Frame(main_frame); self.end_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(5,0))
        time_font_style = ('Segoe UI', 11, 'bold')
        self.start_text_label = ttk.Label(self.start_frame, font=time_font_style); self.start_text_label.pack(side=tk.LEFT, padx=(0, 10))
        self.start_time_slider = ttk.Scale(self.start_frame, from_=0, to=100, orient="horizontal", command=lambda v: self._update_time_from_slider(v, self.start_time_str_var)); self.start_time_slider.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self._create_time_adjust_buttons(self.start_frame, self.start_time_str_var, self.start_time_slider)
        self.end_text_label = ttk.Label(self.end_frame, font=time_font_style); self.end_text_label.pack(side=tk.LEFT, padx=(0, 10))
        self.end_time_slider = ttk.Scale(self.end_frame, from_=0, to=100, orient="horizontal", command=lambda v: self._update_time_from_slider(v, self.end_time_str_var)); self.end_time_slider.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self._create_time_adjust_buttons(self.end_frame, self.end_time_str_var, self.end_time_slider)
        self.settings_label = ttk.Label(main_frame, font=('Segoe UI', 10, 'bold')); self.settings_label.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(15, 5))
        self.filename_text_label = ttk.Label(main_frame, anchor="w"); self.filename_text_label.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(5,0))
        self.filename_entry = ttk.Entry(main_frame, textvariable=self.filename_var); self.filename_entry.grid(row=9, column=0, columnspan=2, sticky="ew", ipady=4)
        self.save_folder_text_label = ttk.Label(main_frame, anchor="w"); self.save_folder_text_label.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(5,0))
        save_path_frame = ttk.Frame(main_frame); save_path_frame.grid(row=11, column=0, columnspan=2, sticky="ew")
        self.save_dir_label = ttk.Label(save_path_frame, textvariable=self.last_save_dir, relief="sunken", anchor="w", padding=5, background="white"); self.save_dir_label.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=1)
        self.browse_button = ttk.Button(save_path_frame, command=self._browse_output_folder); self.browse_button.pack(side=tk.LEFT, padx=(10, 0))
        self.quality_menu = ttk.Combobox(main_frame, textvariable=self.quality_var, values=['Best Video', '1080p', '720p', '480p', '360p', 'Audio Only'], state="readonly"); self.quality_menu.grid(row=12, column=0, columnspan=2, sticky="ew", ipady=4, pady=5)
        cookie_frame = ttk.Frame(main_frame); cookie_frame.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self.cookie_button = ttk.Button(cookie_frame, command=self._browse_cookie_file); self.cookie_button.pack(side=tk.LEFT)
        self.cookie_label = ttk.Label(cookie_frame, textvariable=self.cookie_file_var, foreground="blue", wraplength=350); self.cookie_label.pack(side=tk.LEFT, padx=10)
        self.accuracy_check = ttk.Checkbutton(main_frame, variable=self.high_accuracy_var); self.accuracy_check.grid(row=14, column=0, columnspan=2, sticky="w", pady=(10, 0))
        action_frame = ttk.Frame(main_frame); action_frame.grid(row=15, column=0, columnspan=2, sticky="ew", pady=10)
        self.start_button = ttk.Button(action_frame, command=self._start_download_thread); self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=8)
        self.cancel_button = ttk.Button(action_frame, command=self._cancel_process)
        self.progress_bar = ttk.Progressbar(main_frame, orient='horizontal', mode='determinate'); self.progress_bar.grid(row=16, column=0, columnspan=2, sticky="ew", pady=5)
        self.open_folder_button = ttk.Button(main_frame, command=self._open_containing_folder); self.open_folder_button.grid(row=16, column=0, columnspan=2, sticky="ew", pady=5)
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, wraplength=550, anchor="center"); self.status_label.grid(row=17, column=0, columnspan=2, sticky="ew", pady=5)
        main_frame.columnconfigure(0, weight=1)

    def _execute_ffmpeg(self, ffmpeg_cmd, clip_duration):
        """[إصلاح] تحسين منطق الإلغاء."""
        startupinfo = subprocess.STARTUPINFO() if os.name == 'nt' else None
        if os.name == 'nt': startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
            universal_newlines=True, encoding='utf-8', errors='ignore', startupinfo=startupinfo
        )
        
        time_pattern = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")
        for line in self.ffmpeg_process.stderr:
            # التحقق مما إذا كانت العملية لا تزال قيد التشغيل قبل تحديث الواجهة
            if self.ffmpeg_process.poll() is not None:
                break 
            
            match = time_pattern.search(line)
            if match:
                elapsed_seconds = self._hhmmss_to_seconds(match.group(1))
                percentage = min(100, (elapsed_seconds / clip_duration) * 100)
                self.master.after(0, self.progress_bar.config, {'value': percentage})
                self._update_status("status_clipping", "darkgreen", progress=percentage)
        
        # انتظار انتهاء العملية لمعرفة حالتها النهائية
        self.ffmpeg_process.wait()
        
        # التحقق من الحالة بعد الانتظار
        # إذا كانت العملية لا تزال موجودة ولكن الكود ليس 0، فهذا يعني خطأ
        # إذا كانت None، فهذا يعني أنها أُلغيت عبر terminate()
        if self.ffmpeg_process is None:
            return -9 # رمز مخصص للإلغاء
            
        return self.ffmpeg_process.returncode

    def _cancel_process(self):
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process = None # تعيينها إلى None فورًا
            self._update_status("status_cancelled", "orange")
            # لا حاجة لإعادة تفعيل الأزرار هنا، ستتم إعادتها في finally
            
    def _process_video(self):
        return_code = -1 # قيمة افتراضية
        try:
            save_dir = self.last_save_dir.get()
            clip_duration = max(1, self._hhmmss_to_seconds(self.end_time_str_var.get()) - self._hhmmss_to_seconds(self.start_time_str_var.get()))
            self._update_status("status_fetching_streams", "blue")
            ydl_opts = {'format': self._get_ydl_format(), 'quiet': True}
            if self.cookie_file_var.get(): ydl_opts['cookiefile'] = self.cookie_file_var.get()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: info = ydl.extract_info(self.url_var.get(), download=False)
            is_audio_only = self.quality_var.get() == 'Audio Only'
            output_path = os.path.join(save_dir, self.filename_var.get() + (".m4a" if is_audio_only else ".mp4"))
            ffmpeg_cmd = ['ffmpeg', '-y', '-hide_banner']
            use_high_accuracy = self.high_accuracy_var.get()
            if is_audio_only: ffmpeg_cmd.extend(['-i', info['url']])
            else: ffmpeg_cmd.extend(['-i', info['requested_formats'][0]['url'], '-i', info['requested_formats'][1]['url']])
            if not is_audio_only and use_high_accuracy:
                ffmpeg_cmd.extend(['-ss', self.start_time_str_var.get(), '-to', self.end_time_str_var.get(), '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'aac'])
            else:
                ffmpeg_cmd.extend(['-ss', self.start_time_str_var.get(), '-to', self.end_time_str_var.get(), '-c', 'copy'])
            ffmpeg_cmd.extend(['-v', 'error', '-stats', output_path])
            return_code = self._execute_ffmpeg(ffmpeg_cmd, clip_duration)
            
            # [إصلاح] التحقق من return_code بعد استدعاء الدالة
            if return_code == 0:
                final_path = os.path.abspath(output_path); self.last_download_path = final_path
                self._update_status("status_success", "green", filename=os.path.basename(final_path))
                messagebox.showinfo(self._t("window_title"), f"{self._t('status_success', filename='')}\n{final_path}")
                self.master.after(0, self.progress_bar.grid_remove); self.master.after(0, self.open_folder_button.grid)
                self._save_config()
            elif return_code != -9: # تجاهل رمز الإلغاء
                raise subprocess.CalledProcessError(return_code, "ffmpeg command")
        except Exception as e:
            if self.ffmpeg_process is not None: # لا تظهر رسالة خطأ إذا تم الإلغاء
                error_details = str(e)
                self._update_status("status_error", "red", error=error_details.splitlines()[0])
                messagebox.showerror(self._t("window_title"), f"{self._t('status_error', error='')}\n{error_details}")
        finally:
            self.ffmpeg_process = None
            if hasattr(self, 'start_button'):
                 self.master.after(0, self._set_controls_state, tk.NORMAL)
                 self.master.after(0, self.url_entry.config, {'state': tk.NORMAL})
                 self.master.after(0, self.paste_button.config, {'state': tk.NORMAL})
                 self.master.after(0, self.lang_menu.config, {'state': 'readonly'})
                 self.master.after(0, self.cancel_button.pack_forget)

    # --- باقي الدوال تبقى كما هي ---
    def _set_controls_state(self, state):
        widgets_to_toggle = [self.start_time_slider, self.end_time_slider, self.filename_entry, self.accuracy_check, self.start_button]
        for frame in (self.start_frame, self.end_frame):
            for widget in frame.winfo_children():
                if isinstance(widget, (ttk.Button, ttk.Entry)): widgets_to_toggle.append(widget)
        for widget in widgets_to_toggle: widget.config(state=state)
        self.quality_menu.config(state="readonly" if state == tk.NORMAL else tk.DISABLED)
        self.browse_button.config(state=tk.NORMAL); self.cookie_button.config(state=tk.NORMAL)
    def _change_language(self, event=None):
        self.master.title(self._t("window_title"))
        self.paste_url_label.config(text=self._t("paste_url_label"))
        self.paste_button.config(text=self._t("paste_button"))
        self.select_clip_label.config(text=self._t("select_clip_label"))
        self.start_text_label.config(text=self._t("start_label"))
        self.end_text_label.config(text=self._t("end_label"))
        self.settings_label.config(text=self._t("settings_label"))
        self.filename_text_label.config(text=self._t("filename_label"))
        self.save_folder_text_label.config(text=self._t("save_folder_label"))
        self.browse_button.config(text=self._t("browse_folder_button"))
        self.cookie_button.config(text=self._t("cookie_button"))
        self.accuracy_check.config(text=self._t("accuracy_checkbox"))
        self.start_button.config(text=self._t("start_button"))
        self.cancel_button.config(text=self._t("cancel_button"))
        self.open_folder_button.config(text=self._t("open_folder_button"))
        self._update_status("status_ready", color="gray")
        if self.video_duration > 0: self.video_duration_str_var.set(self._t("video_duration_label", duration=self._seconds_to_hhmmss(self.video_duration)))
        else: self.video_duration_str_var.set(self._t("video_duration_label", duration="--:--:--"))
        if self.last_save_dir.get() in [t.get("save_dir_unselected", "Not selected") for t in self.translations.values()]: self.last_save_dir.set(self._t("save_dir_unselected"))
        self._save_config()
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f: config = json.load(f)
                self.cookie_file_var.set(config.get("cookie_file_path", ""))
                self.current_lang.set(config.get("language", "ar"))
                saved_dir = config.get("last_save_dir")
                if saved_dir: self.last_save_dir.set(saved_dir)
                else: self.last_save_dir.set(self._t("save_dir_unselected"))
            except Exception: self.last_save_dir.set(self._t("save_dir_unselected"))
        self._change_language()
    def _save_config(self):
        save_dir = self.last_save_dir.get()
        if save_dir == self._t("save_dir_unselected"): save_dir = ""
        with open(CONFIG_FILE, 'w') as f: 
            json.dump({"cookie_file_path": self.cookie_file_var.get(), "last_save_dir": save_dir, "language": self.current_lang.get()}, f, indent=2)
    def _update_status(self, text_key, color="black", **kwargs):
        self.status_var.set(self._t(text_key, **kwargs)); self.status_label.config(foreground=color)
    def _reset_ui_for_new_url(self):
        self._set_controls_state(tk.DISABLED)
        self.cancel_button.pack_forget(); self.progress_bar.grid_remove(); self.open_folder_button.grid_remove()
        self.video_duration_str_var.set(self._t("video_duration_label", duration="--:--:--"))
        self.filename_var.set(""); self.last_download_path = ""
        self._update_status("status_ready", color="gray")
    def _setup_ui_after_fetch(self, video_title):
        self._update_status("status_fetch_success", "green")
        self.video_duration_str_var.set(self._t("video_duration_label", duration=self._seconds_to_hhmmss(self.video_duration)))
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", video_title); self.filename_var.set(sanitized_title)
        self.start_time_slider.config(to=self.video_duration); self.end_time_slider.config(to=self.video_duration)
        self._set_controls_state(tk.NORMAL)
        self.start_time_slider.set(0); self.end_time_slider.set(self.video_duration)
        self.start_time_str_var.set(self._seconds_to_hhmmss(0)); self.end_time_str_var.set(self._seconds_to_hhmmss(self.video_duration))
    def _on_url_change(self, event=None):
        if self.after_id: self.master.after_cancel(self.after_id)
        if "http" in self.url_var.get(): self._reset_ui_for_new_url(); self._update_status("status_checking", "blue"); self.after_id = self.master.after(700, self._start_fetch_info_thread)
    def _fetch_video_info(self, url):
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            if self.cookie_file_var.get(): ydl_opts['cookiefile'] = self.cookie_file_var.get()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: info = ydl.extract_info(url, download=False)
            self.video_duration = info.get('duration', 0); video_title = info.get('title', 'video')
            if self.video_duration > 0: self.master.after(0, self._setup_ui_after_fetch, video_title)
            else: raise ValueError("Video duration not found.")
        except Exception as e: self._update_status("status_error", "red", error=str(e).splitlines()[0])
    def _start_download_thread(self):
        if not self.filename_var.get() or not self.last_save_dir.get() or self.last_save_dir.get() == self._t("save_dir_unselected"):
            messagebox.showwarning(self._t("window_title"), self._t("error_no_filename")); return
        start_s = self._hhmmss_to_seconds(self.start_time_str_var.get()); end_s = self._hhmmss_to_seconds(self.end_time_str_var.get())
        if end_s <= start_s:
            messagebox.showerror(self._t("window_title"), self._t("error_time_issue")); return
        self._set_controls_state(tk.DISABLED)
        self.url_entry.config(state=tk.DISABLED); self.paste_button.config(state=tk.DISABLED); self.lang_menu.config(state=tk.DISABLED)
        self.cancel_button.pack(side=tk.RIGHT, expand=True, fill=tk.X, ipady=8, padx=(10,0))
        self.progress_bar.grid(); self.open_folder_button.grid_remove()
        self.progress_bar['value'] = 0; threading.Thread(target=self._process_video, daemon=True).start()
    def _on_closing(self):
        if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
            if messagebox.askyesno(self._t("confirm_exit_title"), self._t("confirm_exit_msg")):
                self.ffmpeg_process.terminate(); self.master.destroy()
        else: self.master.destroy()
    def _create_time_adjust_buttons(self, parent_frame, time_var, slider):
        btn_minus = ttk.Button(parent_frame, text="-", width=3); btn_minus.pack(side=tk.LEFT, padx=(10, 0))
        time_entry = ttk.Entry(parent_frame, textvariable=time_var, width=9, font=('Segoe UI', 11, 'bold'), justify='center'); time_entry.pack(side=tk.LEFT, padx=5)
        btn_plus = ttk.Button(parent_frame, text="+", width=3); btn_plus.pack(side=tk.LEFT)
        btn_plus.bind('<ButtonPress-1>', lambda e: self._start_repeat(time_var, slider, 1)); btn_plus.bind('<ButtonRelease-1>', self._stop_repeat)
        btn_minus.bind('<ButtonPress-1>', lambda e: self._start_repeat(time_var, slider, -1)); btn_minus.bind('<ButtonRelease-1>', self._stop_repeat)
        time_entry.bind("<FocusOut>", lambda e: self._format_and_update_from_entry(time_var, slider)); time_entry.bind("<Return>", lambda e: self._format_and_update_from_entry(time_var, slider))
    def _start_repeat(self, time_var, slider, delta): self._adjust_time(time_var, slider, delta); self.repeat_job = self.master.after(400, lambda: self._repeat_action(time_var, slider, delta))
    def _repeat_action(self, time_var, slider, delta):
        if self.repeat_job: self._adjust_time(time_var, slider, delta); self.repeat_job = self.master.after(100, lambda: self._repeat_action(time_var, slider, delta))
    def _stop_repeat(self, event=None):
        if self.repeat_job: self.master.after_cancel(self.repeat_job); self.repeat_job = None
    def _adjust_time(self, time_var, slider, delta):
        new_seconds = min(self.video_duration, max(0, self._hhmmss_to_seconds(time_var.get()) + delta))
        time_var.set(self._seconds_to_hhmmss(new_seconds)); slider.set(new_seconds)
    def _format_and_update_from_entry(self, time_var, slider):
        time_str = time_var.get(); numbers = "".join(filter(str.isdigit, time_str))
        if not numbers: numbers = "0"
        seconds = 0
        if len(numbers) <= 2: seconds = int(numbers)
        elif len(numbers) <= 4: seconds = int(numbers[:-2]) * 60 + int(numbers[-2:])
        else: seconds = int(numbers[:-4]) * 3600 + int(numbers[-4:-2]) * 60 + int(numbers[-2:])
        seconds = min(self.video_duration, max(0, seconds)); time_var.set(self._seconds_to_hhmmss(seconds)); slider.set(seconds)
    def _update_time_from_slider(self, value, time_var): time_var.set(self._seconds_to_hhmmss(value))
    def _paste_from_clipboard(self):
        try: self.url_var.set(self.master.clipboard_get()); self._on_url_change()
        except tk.TclError: self._update_status("status_clipboard_empty", "orange")
    def _open_containing_folder(self):
        if not self.last_download_path or not os.path.exists(self.last_download_path):
            messagebox.showwarning(self._t("window_title"), self._t("folder_not_found")); return
        try:
            if sys.platform == "win32": subprocess.run(['explorer', '/select,', self.last_download_path])
            elif sys.platform == "darwin": subprocess.run(['open', '-R', self.last_download_path])
            else: subprocess.run(['xdg-open', os.path.dirname(self.last_download_path)])
        except Exception as e: messagebox.showerror(self._t("window_title"), self._t("folder_open_error", error=e))
    def _seconds_to_hhmmss(self, seconds): s = int(float(seconds)); return f"{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}"
    def _hhmmss_to_seconds(self, t_str):
        try: parts = list(map(int, t_str.split('.')[0].split(':'))); return parts[0]*3600+parts[1]*60+parts[2] if len(parts)==3 else 0
        except (ValueError, IndexError): return 0
    def _browse_cookie_file(self):
        filepath = filedialog.askopenfilename(title=self._t("cookie_button"), filetypes=[("Text files", "*.txt")])
        if filepath: self.cookie_file_var.set(filepath); self._save_config(); self._update_status("status_cookie_selected", "blue", filename=os.path.basename(filepath))
    def _browse_output_folder(self):
        initial_dir = self.last_save_dir.get() if self.last_save_dir.get() != self._t("save_dir_unselected") else os.getcwd()
        dir_path = filedialog.askdirectory(title=self._t("browse_folder_button"), initialdir=initial_dir)
        if dir_path:
            self.last_save_dir.set(dir_path)
            self._save_config()
            self._update_status("status_folder_selected", "blue", path=dir_path)
    def _check_ffmpeg(self):
        try:
            info = subprocess.STARTUPINFO() if os.name == 'nt' else None
            if os.name == 'nt': info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(['ffmpeg', "-version"], check=True, capture_output=True, startupinfo=info)
        except FileNotFoundError: messagebox.showerror("FFmpeg Error", "FFmpeg not found. Please install it and add to your system's PATH."); self.master.destroy()
    def _get_ydl_format(self):
        q = self.quality_var.get()
        if q == 'Audio Only': return 'bestaudio[ext=m4a]/bestaudio/best'
        if q == 'Best Video': return 'bestvideo+bestaudio/best';
        return f"bestvideo[height<={q.replace('p','') }]+bestaudio/best"
    def _start_fetch_info_thread(self): threading.Thread(target=self._fetch_video_info, args=(self.url_var.get(),), daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = MohyDownloaderApp(root)
    root.mainloop()