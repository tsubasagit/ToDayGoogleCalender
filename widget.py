import tkinter as tk
import datetime
import threading
import webbrowser
import winsound
from zoneinfo import ZoneInfo
import pystray
from PIL import Image, ImageDraw
from calendar_api import get_events_for_date, is_logged_in, login, logout


class CalendarWidget:
    # 色定義
    BG_COLOR = "#1e1e2e"
    FG_COLOR = "#cdd6f4"
    HEADER_BG = "#313244"
    ACCENT_COLOR = "#89b4fa"
    CURRENT_BG = "#45475a"
    CURRENT_FG = "#f5e0dc"
    TIME_COLOR = "#a6adc8"
    LOCATION_COLOR = "#6c7086"
    ALLDAY_BG = "#585b70"
    BORDER_COLOR = "#45475a"
    NAV_BG = "#313244"
    ALERT_ON_COLOR = "#f9e2af"
    ALERT_OFF_COLOR = "#6c7086"
    LINK_COLOR = "#74c7ec"

    ALERT_CHECK_MS = 30 * 1000  # 30秒ごとにアラートチェック
    ALERT_MINUTES_BEFORE = 5    # 何分前に通知するか

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calendar Widget")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)
        self.root.configure(bg=self.BG_COLOR)

        self.topmost = True
        self.events = []
        self.tray_icon = None
        self.cal_tz = None  # Googleカレンダーのタイムゾーン
        self.display_date = datetime.date.today()
        self.alert_enabled = False
        self._alerted_events = set()  # 既にアラート済みのイベント(start時刻文字列)

        # ウィンドウサイズと位置
        self.width = 320
        self.root.geometry(f"{self.width}x400+100+100")

        # ドラッグ用
        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()
        self._setup_tray_icon()
        self._check_alerts()

        # ログイン状態チェック
        if is_logged_in():
            self._refresh_events()
        else:
            self._show_login_screen()

    def _build_ui(self):
        # === ヘッダー（ドラッグ + ボタン群） ===
        self.header = tk.Frame(self.root, bg=self.HEADER_BG, cursor="fleur")
        self.header.pack(fill=tk.X)
        self.header.bind("<ButtonPress-1>", self._on_drag_start)
        self.header.bind("<B1-Motion>", self._on_drag_motion)

        # 閉じるボタン (右端)
        close_btn = tk.Label(
            self.header, text=" \u2715 ", bg=self.HEADER_BG, fg=self.TIME_COLOR,
            font=("Segoe UI", 10), cursor="hand2", pady=6,
        )
        close_btn.pack(side=tk.RIGHT, padx=(0, 4))
        close_btn.bind("<Button-1>", lambda e: self._hide_to_tray())

        # 設定ボタン（ギア）
        settings_btn = tk.Label(
            self.header, text=" \u2699 ", bg=self.HEADER_BG, fg=self.TIME_COLOR,
            font=("Segoe UI", 11), cursor="hand2", pady=6,
        )
        settings_btn.pack(side=tk.RIGHT)
        settings_btn.bind("<Button-1>", lambda e: self._show_settings())

        # 更新ボタン
        refresh_btn = tk.Label(
            self.header, text=" \u21bb ", bg=self.HEADER_BG, fg=self.TIME_COLOR,
            font=("Segoe UI", 11), cursor="hand2", pady=6,
        )
        refresh_btn.pack(side=tk.RIGHT)
        refresh_btn.bind("<Button-1>", lambda e: self._refresh_events())

        # アラートトグルボタン
        self.alert_btn = tk.Label(
            self.header, text=" \U0001f514 ", bg=self.HEADER_BG,
            fg=self.ALERT_OFF_COLOR, font=("Segoe UI", 10), cursor="hand2", pady=6,
        )
        self.alert_btn.pack(side=tk.RIGHT)
        self.alert_btn.bind("<Button-1>", lambda e: self._toggle_alert())
        self.alert_btn.bind("<Enter>", self._show_alert_tooltip)
        self.alert_btn.bind("<Leave>", self._hide_alert_tooltip)
        self._tooltip = None

        # 日付ラベル (ドラッグ可能)
        self.date_label = tk.Label(
            self.header, text="", bg=self.HEADER_BG, fg=self.ACCENT_COLOR,
            font=("Segoe UI", 11, "bold"), anchor="w", pady=6, padx=6,
        )
        self.date_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.date_label.bind("<ButtonPress-1>", self._on_drag_start)
        self.date_label.bind("<B1-Motion>", self._on_drag_motion)

        # === 日付ナビゲーションバー ===
        self.nav_bar = tk.Frame(self.root, bg=self.NAV_BG)
        self.nav_bar.pack(fill=tk.X)

        prev_btn = tk.Label(
            self.nav_bar, text=" \u25c0 前日 ", bg=self.NAV_BG, fg=self.FG_COLOR,
            font=("Segoe UI", 9), cursor="hand2", pady=4,
        )
        prev_btn.pack(side=tk.LEFT, padx=(8, 0))
        prev_btn.bind("<Button-1>", lambda e: self._change_date(-1))

        self.today_btn = tk.Label(
            self.nav_bar, text=" 今日 ", bg=self.NAV_BG, fg=self.ACCENT_COLOR,
            font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4,
        )
        self.today_btn.pack(side=tk.LEFT, expand=True)
        self.today_btn.bind("<Button-1>", lambda e: self._go_today())

        next_btn = tk.Label(
            self.nav_bar, text=" 翌日 \u25b6 ", bg=self.NAV_BG, fg=self.FG_COLOR,
            font=("Segoe UI", 9), cursor="hand2", pady=4,
        )
        next_btn.pack(side=tk.RIGHT, padx=(0, 8))
        next_btn.bind("<Button-1>", lambda e: self._change_date(1))

        # 境界線
        tk.Frame(self.root, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X)

        # === イベント表示エリア ===
        self.canvas = tk.Canvas(
            self.root, bg=self.BG_COLOR, highlightthickness=0, width=self.width
        )
        self.events_frame = tk.Frame(self.canvas, bg=self.BG_COLOR)

        self.events_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window(
            (0, 0), window=self.events_frame, anchor="nw", width=self.width
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # === フッター（Google Calendar リンク） ===
        self.footer = tk.Frame(self.root, bg=self.BG_COLOR)
        self.footer.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Frame(self.footer, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X)
        gcal_link = tk.Label(
            self.footer, text="Google Calendar \u2197", bg=self.BG_COLOR,
            fg=self.LINK_COLOR, font=("Segoe UI", 8, "underline"),
            cursor="hand2", pady=4,
        )
        gcal_link.pack(anchor="e", padx=8)
        gcal_link.bind("<Button-1>", lambda e: self._open_google_calendar())

        # === 右クリックメニュー ===
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="更新", command=self._refresh_events)
        self.context_menu.add_command(label="今日に戻る", command=self._go_today)
        self.context_menu.add_command(label="最前面 ON/OFF", command=self._toggle_topmost)
        self.context_menu.add_command(label="ログアウト", command=self._do_logout)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="終了", command=self._quit)
        self.root.bind("<Button-3>", self._show_context_menu)

        self._update_date_label()

    # === 日付ナビゲーション ===

    def _change_date(self, delta):
        self.display_date += datetime.timedelta(days=delta)
        self._update_date_label()
        self._refresh_events()

    def _go_today(self):
        self.display_date = datetime.date.today()
        self._update_date_label()
        self._refresh_events()

    def _update_date_label(self):
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        d = self.display_date
        date_str = f"{d.year}/{d.month:02d}/{d.day:02d} ({weekdays[d.weekday()]})"

        today = datetime.date.today()
        if d == today:
            prefix = "今日"
        elif d == today - datetime.timedelta(days=1):
            prefix = "昨日"
        elif d == today + datetime.timedelta(days=1):
            prefix = "明日"
        else:
            prefix = ""

        if prefix:
            self.date_label.configure(text=f" {prefix}  {date_str}")
        else:
            self.date_label.configure(text=f" {date_str}")

    # === ツールチップ ===

    def _show_alert_tooltip(self, event):
        if self._tooltip:
            return
        x = self.alert_btn.winfo_rootx()
        y = self.alert_btn.winfo_rooty() + self.alert_btn.winfo_height() + 4
        self._tooltip = tw = tk.Toplevel(self.root)
        tw.overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.geometry(f"+{x}+{y}")
        tk.Label(
            tw, text="5分前にアラートが鳴ります", bg="#585b70", fg=self.FG_COLOR,
            font=("Segoe UI", 8), padx=8, pady=4,
        ).pack()

    def _hide_alert_tooltip(self, event):
        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None

    # === アラート機能 ===

    def _toggle_alert(self):
        self.alert_enabled = not self.alert_enabled
        if self.alert_enabled:
            self.alert_btn.configure(fg=self.ALERT_ON_COLOR)
            self._alerted_events.clear()
        else:
            self.alert_btn.configure(fg=self.ALERT_OFF_COLOR)

    def _check_alerts(self):
        if self.alert_enabled and self.events:
            now = self._get_now()
            for event in self.events:
                if event.get("all_day") or "error" in event:
                    continue
                try:
                    start_dt = datetime.datetime.fromisoformat(event["start"])
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=self.cal_tz) if self.cal_tz else start_dt.astimezone()
                    diff = (start_dt - now).total_seconds() / 60
                    key = event["start"] + event["summary"]
                    if 0 < diff <= self.ALERT_MINUTES_BEFORE and key not in self._alerted_events:
                        self._alerted_events.add(key)
                        self._show_alert(event, int(diff))
                except (ValueError, KeyError):
                    pass

        self.root.after(self.ALERT_CHECK_MS, self._check_alerts)

    def _show_alert(self, event, minutes_left):
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

        alert_win = tk.Toplevel(self.root)
        alert_win.overrideredirect(True)
        alert_win.attributes("-topmost", True)
        alert_win.configure(bg="#f38ba8")

        x = self.root.winfo_x()
        y = self.root.winfo_y() - 80
        alert_win.geometry(f"{self.width}x70+{x}+{y}")

        tk.Label(
            alert_win, text=f"あと{minutes_left}分", bg="#f38ba8", fg="#1e1e2e",
            font=("Segoe UI", 9, "bold"), anchor="w",
        ).pack(fill=tk.X, padx=10, pady=(8, 0))

        tk.Label(
            alert_win, text=event["summary"], bg="#f38ba8", fg="#1e1e2e",
            font=("Segoe UI", 11, "bold"), anchor="w",
        ).pack(fill=tk.X, padx=10)

        close_label = tk.Label(
            alert_win, text="\u2715", bg="#f38ba8", fg="#1e1e2e",
            font=("Segoe UI", 10), cursor="hand2",
        )
        close_label.place(relx=1.0, x=-24, y=4)
        close_label.bind("<Button-1>", lambda e: alert_win.destroy())

        alert_win.after(15000, alert_win.destroy)

    # === Google Calendar リンク ===

    def _open_google_calendar(self):
        d = self.display_date
        url = f"https://calendar.google.com/calendar/r/day/{d.year}/{d.month}/{d.day}"
        webbrowser.open(url)

    # === ドラッグ ===

    def _on_drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag_motion(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _toggle_topmost(self):
        self.topmost = not self.topmost
        self.root.attributes("-topmost", self.topmost)

    # === ログイン画面 ===

    def _show_login_screen(self):
        for widget in self.events_frame.winfo_children():
            widget.destroy()

        tk.Label(
            self.events_frame, text="Googleにログインしてください",
            bg=self.BG_COLOR, fg=self.FG_COLOR,
            font=("Segoe UI", 10), pady=16,
        ).pack(fill=tk.X)

        tk.Label(
            self.events_frame,
            text="カレンダーの予定を取得するには\nGoogleアカウントの認証が必要です",
            bg=self.BG_COLOR, fg=self.TIME_COLOR,
            font=("Segoe UI", 8), justify=tk.CENTER,
        ).pack(fill=tk.X, padx=10)

        login_btn = tk.Label(
            self.events_frame, text="  ログイン  ", bg=self.ACCENT_COLOR,
            fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
            cursor="hand2", pady=8,
        )
        login_btn.pack(pady=16)
        login_btn.bind("<Button-1>", lambda e: self._do_login())

        self._update_window_height()

    def _do_login(self):
        for widget in self.events_frame.winfo_children():
            widget.destroy()
        tk.Label(
            self.events_frame, text="ブラウザで認証中...",
            bg=self.BG_COLOR, fg=self.TIME_COLOR,
            font=("Segoe UI", 9), pady=20,
        ).pack(fill=tk.X)
        self._update_window_height()

        def run_login():
            try:
                login()
                self.root.after(0, self._refresh_events)
            except Exception as e:
                self.root.after(0, lambda: self._update_display([{"error": str(e)}]))

        threading.Thread(target=run_login, daemon=True).start()

    def _do_logout(self):
        """ログアウトしてログイン画面を表示する。"""
        logout()
        self._show_login_screen()

    def _show_settings(self):
        """設定ウィンドウを表示する。"""
        tw = tk.Toplevel(self.root)
        tw.title("設定")
        tw.overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.configure(bg=self.BG_COLOR)
        tw.geometry("280x240")
        x = self.root.winfo_x() + (self.width - 280) // 2
        y = self.root.winfo_y() + 60
        tw.geometry(f"280x240+{x}+{y}")

        def close_settings():
            tw.destroy()

        # ヘッダー（閉じるボタン）
        header = tk.Frame(tw, bg=self.HEADER_BG)
        header.pack(fill=tk.X)
        close_label = tk.Label(
            header, text=" \u2715 ", bg=self.HEADER_BG, fg=self.TIME_COLOR,
            font=("Segoe UI", 10), cursor="hand2", pady=4,
        )
        close_label.pack(side=tk.RIGHT)
        close_label.bind("<Button-1>", lambda e: close_settings())
        tk.Label(
            header, text=" 設定 ", bg=self.HEADER_BG, fg=self.ACCENT_COLOR,
            font=("Segoe UI", 10, "bold"), anchor="w",
        ).pack(side=tk.LEFT)
        tk.Frame(tw, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X)

        # 設定内容
        frame = tk.Frame(tw, bg=self.BG_COLOR, padx=16, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame, text="現在のアカウント",
            bg=self.BG_COLOR, fg=self.TIME_COLOR,
            font=("Segoe UI", 8), anchor="w",
        ).pack(fill=tk.X)
        account_text = "Googleでログイン中" if is_logged_in() else "未ログイン"
        tk.Label(
            frame, text=account_text,
            bg=self.BG_COLOR, fg=self.FG_COLOR,
            font=("Segoe UI", 9), anchor="w",
        ).pack(fill=tk.X)
        tk.Frame(frame, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X, pady=(0, 12))

        logout_label = tk.Label(
            frame, text="ログアウト", bg=self.BG_COLOR, fg=self.ACCENT_COLOR,
            font=("Segoe UI", 9, "underline"), cursor="hand2", anchor="w",
        )
        logout_label.pack(fill=tk.X)
        logout_label.bind("<Button-1>", lambda e: (close_settings(), self._do_logout()))
        tk.Frame(frame, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            frame, text="サービス名  TodayGoogleCalender",
            bg=self.BG_COLOR, fg=self.TIME_COLOR,
            font=("Segoe UI", 8), anchor="w",
        ).pack(fill=tk.X)
        tk.Label(
            frame, text="作成者: tsubasa_miyazaki",
            bg=self.BG_COLOR, fg=self.TIME_COLOR,
            font=("Segoe UI", 8), anchor="w",
        ).pack(fill=tk.X)
        tk.Label(
            frame, text="AppTalentHub",
            bg=self.BG_COLOR, fg=self.ACCENT_COLOR,
            font=("Segoe UI", 8), anchor="w",
        ).pack(fill=tk.X)

    # === イベント取得・表示 ===

    def _refresh_events(self):
        target = self.display_date

        def fetch():
            try:
                result = get_events_for_date(target)
                events = result["events"]
                tz_name = result["timezone"]
            except FileNotFoundError as e:
                events = [{"error": str(e)}]
                tz_name = None
            except Exception as e:
                events = [{"error": f"エラー: {e}"}]
                tz_name = None
            self.root.after(0, lambda: self._on_events_fetched(events, tz_name))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_events_fetched(self, events, tz_name):
        if tz_name:
            self.cal_tz = ZoneInfo(tz_name)
        self.events = events
        self._update_display(events)

    def _get_now(self):
        """カレンダーのタイムゾーンでの現在時刻を返す。"""
        if self.cal_tz:
            return datetime.datetime.now(self.cal_tz)
        return datetime.datetime.now(datetime.timezone.utc).astimezone()

    def _get_today(self):
        """カレンダーのタイムゾーンでの今日の日付を返す。"""
        return self._get_now().date()

    def _update_display(self, events):
        for widget in self.events_frame.winfo_children():
            widget.destroy()

        if events and "error" in events[0]:
            tk.Label(
                self.events_frame, text=events[0]["error"], bg=self.BG_COLOR,
                fg="#f38ba8", font=("Segoe UI", 9), wraplength=self.width - 20,
                justify=tk.LEFT, padx=10, pady=20,
            ).pack(fill=tk.X)
            self._update_window_height()
            return

        now = self._get_now()
        is_today = self.display_date == self._get_today()

        # 今日表示の場合、終了済みの予定をフィルタ
        visible_events = []
        for event in events:
            if is_today and not event.get("all_day", False):
                try:
                    end_dt = datetime.datetime.fromisoformat(event["end"])
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=self.cal_tz) if self.cal_tz else end_dt.astimezone()
                    if end_dt < now:
                        continue  # 過ぎた予定はスキップ
                except (ValueError, KeyError):
                    pass
            visible_events.append(event)

        if not visible_events:
            msg = "残りの予定はありません" if is_today and events else "予定はありません"
            tk.Label(
                self.events_frame, text=msg, bg=self.BG_COLOR,
                fg=self.TIME_COLOR, font=("Segoe UI", 10), pady=20,
            ).pack(fill=tk.X)
            self._update_window_height()
            return

        for event in visible_events:
            is_current = False
            all_day = event.get("all_day", False)

            if not all_day and is_today:
                try:
                    start_dt = datetime.datetime.fromisoformat(event["start"])
                    end_dt = datetime.datetime.fromisoformat(event["end"])
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=self.cal_tz) if self.cal_tz else start_dt.astimezone()
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=self.cal_tz) if self.cal_tz else end_dt.astimezone()
                    is_current = start_dt <= now <= end_dt
                except (ValueError, KeyError):
                    pass

            bg = self.CURRENT_BG if is_current else self.BG_COLOR

            card = tk.Frame(self.events_frame, bg=bg)
            card.pack(fill=tk.X, padx=6, pady=2)

            bar_color = self.CURRENT_FG if is_current else self.ACCENT_COLOR
            tk.Frame(card, bg=bar_color, width=3).pack(
                side=tk.LEFT, fill=tk.Y, padx=(0, 8), pady=4
            )

            content = tk.Frame(card, bg=bg)
            content.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=4)

            if all_day:
                time_str = "終日"
                time_bg = self.ALLDAY_BG
            else:
                try:
                    s = datetime.datetime.fromisoformat(event["start"])
                    e = datetime.datetime.fromisoformat(event["end"])
                    time_str = f"{s.strftime('%H:%M')} - {e.strftime('%H:%M')}"
                except (ValueError, KeyError):
                    time_str = ""
                time_bg = bg

            if time_str:
                tk.Label(
                    content, text=time_str,
                    bg=time_bg if all_day else bg,
                    fg=self.FG_COLOR if all_day else self.TIME_COLOR,
                    font=("Segoe UI", 8), anchor="w",
                    padx=2 if all_day else 0,
                ).pack(anchor="w")

            title_fg = self.CURRENT_FG if is_current else self.FG_COLOR
            tk.Label(
                content, text=event["summary"], bg=bg, fg=title_fg,
                font=("Segoe UI", 10, "bold") if is_current else ("Segoe UI", 10),
                anchor="w", wraplength=self.width - 40, justify=tk.LEFT,
            ).pack(anchor="w")

            if event.get("location"):
                tk.Label(
                    content, text=f"\U0001f4cd {event['location']}", bg=bg,
                    fg=self.LOCATION_COLOR, font=("Segoe UI", 8), anchor="w",
                    wraplength=self.width - 40, justify=tk.LEFT,
                ).pack(anchor="w")

            tk.Frame(self.events_frame, bg=self.BORDER_COLOR, height=1).pack(
                fill=tk.X, padx=10
            )

        self._update_window_height()

    def _update_window_height(self):
        self.root.update_idletasks()
        header_h = self.header.winfo_reqheight()
        nav_h = self.nav_bar.winfo_reqheight()
        footer_h = self.footer.winfo_reqheight()
        content_h = self.events_frame.winfo_reqheight()
        fixed_h = header_h + nav_h + footer_h + 2  # borders
        max_content = 400
        canvas_h = min(content_h, max_content)
        total_h = fixed_h + canvas_h
        self.canvas.configure(height=canvas_h)
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{self.width}x{total_h}+{x}+{y}")

    # === システムトレイ ===

    def _create_tray_image(self):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([8, 16, 56, 56], fill="#89b4fa", outline="#313244", width=2)
        draw.rectangle([8, 16, 56, 28], fill="#f38ba8")
        draw.text((22, 30), str(datetime.date.today().day), fill="#1e1e2e")
        return img

    def _setup_tray_icon(self):
        image = self._create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("表示", self._show_from_tray, default=True),
            pystray.MenuItem("更新", lambda: self.root.after(0, self._refresh_events)),
            pystray.MenuItem("終了", self._quit_from_tray),
        )
        self.tray_icon = pystray.Icon("calendar_widget", image, "今日の予定", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _hide_to_tray(self):
        self.root.withdraw()

    def _show_from_tray(self):
        self.root.after(0, self.root.deiconify)

    def _quit_from_tray(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def _quit(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
