import tkinter as tk
from datetime import datetime
import asyncio
import threading
from suntime import Sun

from config import LATITUDE, LONGITUDE, DAYS, COLORS
from ble_controller import BLEController
from gui.gui1 import setup_gui1
from gui.gui2 import setup_gui2

class LEDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LED-Irányító 2000")
        self.root.geometry("1000x800")
        self.root.configure(bg='#f4e7da')
        self.center_window()

        self.devices = []
        self.selected_device = None
        self.connected = False
        self.last_color_hex = COLORS[0][2]
        self.is_led_on = True
        self.follow_dst = tk.BooleanVar(value=False)
        self.sun = Sun(LATITUDE, LONGITUDE)
        self.last_activity = datetime.now()

        self.schedule = {day: {"color": "", "on_time": "", "off_time": "",
                               "sunrise": False, "sunrise_offset": 0,
                               "sunset": False, "sunset_offset": 0} for day in DAYS}

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

        self.ble = BLEController()

        # GUI1 indítása
        setup_gui1(self)

    def center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")
        
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def load_gui1(self):
        from gui.gui1 import setup_gui1
        setup_gui1(self)



    def disconnect_device(self):
        async def do_disconnect():
            try:
                await self.ble.disconnect()
                self.connected = False
                self.selected_device = None
                self.root.after(0, lambda: self.load_gui1())
            except Exception as e:
                self.root.after(0, lambda err=e: messagebox.showerror("Hiba", f"Nem sikerült bontani: {err}"))
        asyncio.run_coroutine_threadsafe(do_disconnect(), self.loop)

