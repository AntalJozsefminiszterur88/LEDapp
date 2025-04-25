import tkinter as tk
from tkinter import ttk, messagebox
import asyncio

from config import COLORS
from gui.gui2 import setup_gui2

def setup_gui1(app):
    app.clear_window()
    app.root.title("LED-Irányító 2000 - Csatlakozás")
    app.root.configure(bg='#f4e7da')

    main_frame = tk.Frame(app.root, bg='#f4e7da')
    main_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    tk.Label(main_frame, text="LED ESZKÖZ KERESÉSE", font=("Arial", 16, "bold"), bg='#f4e7da').pack(pady=10)

    # Progress bar
    app.progress_frame = tk.Frame(main_frame, bg='#f4e7da')
    app.progress_frame.pack(pady=5)

    app.progress_label = tk.Label(app.progress_frame, text="", font=("Arial", 10), bg='#f4e7da', fg="gray")
    app.progress_label.pack(side=tk.LEFT)

    app.progress_bar = ttk.Progressbar(app.progress_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
    app.progress_bar.pack(side=tk.LEFT, padx=5)

    app.device_listbox = tk.Listbox(main_frame, width=60, height=10, font=("Arial", 12), selectbackground="#a6a6a6")
    app.device_listbox.pack(padx=20, pady=10)
    app.device_listbox.bind("<Double-Button-1>", lambda event: on_device_double_click(app))

    button_frame = tk.Frame(main_frame, bg='#f4e7da')
    button_frame.pack(pady=10)

    # Keresés gomb
    tk.Button(button_frame, text="Keresés", font=("Arial", 12),
              command=lambda: search_devices(app)).pack(side=tk.LEFT, padx=5)

    # Kapcsolat gombok feltételes megjelenítése
    if app.connected:
        tk.Button(button_frame, text="Kapcsolat bontása", font=("Arial", 12),
                  command=app.disconnect_device).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="→", font=("Arial", 12),
                  command=lambda: setup_gui2(app)).pack(side=tk.LEFT, padx=5)
    else:
        tk.Button(button_frame, text="Csatlakozás", font=("Arial", 12),
                  command=lambda: connect_device(app)).pack(side=tk.LEFT, padx=5)

    if app.devices:
        update_device_list(app)


def update_device_list(app):
    app.device_listbox.delete(0, tk.END)
    for name, addr in app.devices:
        app.device_listbox.insert(tk.END, f"{name} ({addr})")


def on_device_double_click(app):
    selection = app.device_listbox.curselection()
    if selection:
        connect_device(app)


def search_devices(app):  # Typo: search_devices helyett search_devices
    async def async_scan_devices():
        app.progress_label.config(text="Keresés folyamatban...")
        app.progress_bar['value'] = 0
        app.root.update()

        try:
            devices = await app.ble.scan()
            app.devices = devices

            for i in range(5):
                app.progress_bar['value'] += 20
                app.root.update()
                await asyncio.sleep(0.1)

            update_device_list(app)
            app.progress_label.config(text=f"{len(app.devices)} eszköz található")
        except Exception as e:
            app.progress_label.config(text=f"Hiba: {str(e)}")
        finally:
            app.progress_bar['value'] = 100

    asyncio.run_coroutine_threadsafe(async_scan_devices(), app.loop)


def connect_device(app):
    selection = app.device_listbox.curselection()
    if not selection:
        messagebox.showwarning("Nincs kiválasztva", "Kérlek válassz ki egy eszközt a listából.")
        return

    index = selection[0]
    app.selected_device = app.devices[index]
    app.progress_label.config(text="Csatlakozás folyamatban...")
    app.progress_bar['value'] = 0

    async def do_connect():
        try:
            for i in range(5):
                app.progress_bar['value'] += 10
                app.root.update()
                await asyncio.sleep(0.1)

            success = await asyncio.wait_for(app.ble.connect(app.selected_device[1]), timeout=10)

            for i in range(5):
                app.progress_bar['value'] += 10
                app.root.update()
                await asyncio.sleep(0.1)

            if success:
                app.connected = True
                app.root.after(0, lambda: setup_gui2(app))
            else:
                messagebox.showerror("Hiba", "Nem sikerült csatlakozni az eszközhöz.")
        except asyncio.TimeoutError:
            app.root.after(0, lambda: messagebox.showerror("Időtúllépés", "A csatlakozás túllépte az időkorlátot."))
        except Exception as e:
            app.root.after(0, lambda err=e: messagebox.showerror("Hiba", f"Nem sikerült csatlakozni: {err}"))
        finally:
            app.progress_bar['value'] = 100
            app.progress_label.config(text="")

    asyncio.run_coroutine_threadsafe(do_connect(), app.loop)
