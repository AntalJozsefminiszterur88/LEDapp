import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import geocoder
import asyncio
import json
import os
from suntime import Sun

from config import COLORS, DAYS, CONFIG_FILE, TIMEZONE

def get_gps_location():
    """GPS koordináták lekérése IP cím alapján"""
    try:
        g = geocoder.ip('me')
        if g.latlng:
            return g.latlng[0], g.latlng[1]
        return (47.4979, 19.0402)  # Alapértelmezett Budapest
    except Exception:
        return (47.4979, 19.0402)  # Hiba esetén Budapest

def setup_gui2(app):
    app.clear_window()
    app.root.title(f"LED-Irányító 2000 - {app.selected_device[0] if app.selected_device else ''}")
    app.root.configure(bg='#f4e7da')
    main_frame = tk.Frame(app.root, bg='#f4e7da')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # GPS adatok lekérése
    latitude, longitude = get_gps_location()
    sun = Sun(latitude, longitude)
    now = datetime.now()

    # Napkelte/naplemente számítás
    try:
        sunrise = sun.get_local_sunrise_time(now)
        sunset = sun.get_local_sunset_time(now)
    except Exception:
        sunrise = now.replace(hour=6, minute=0)
        sunset = now.replace(hour=18, minute=0)

    # Eszköznév
    device_frame = tk.Frame(main_frame, bg='#f4e7da')
    device_frame.pack(fill=tk.X, pady=5)
    tk.Label(device_frame, text=f"Csatlakoztatott eszköz: {app.selected_device[0]}", 
             font=("Arial", 12), bg='#f4e7da').pack(side=tk.LEFT)

    # DST kapcsoló
    dst_frame = tk.Frame(device_frame, bg='#f4e7da')
    dst_frame.pack(side=tk.RIGHT)
    tk.Checkbutton(dst_frame, text="Óraátállítás követése", variable=app.follow_dst,
                   font=("Arial", 10, "bold"), bg='#f4e7da').pack()

    # Valós idejű óra
    time_frame = tk.Frame(main_frame, bg='#f4e7da')
    time_frame.pack(fill=tk.X, pady=10)
    app.time_label = tk.Label(time_frame, text="", font=("Arial", 12), bg='#f4e7da')
    app.time_label.pack()

    # Napkelte és koordináták
    sun_frame = tk.Frame(main_frame, bg='#f4e7da')
    sun_frame.pack(fill=tk.X, pady=5)
    tk.Label(sun_frame, 
             text=f"Napkelte: {sunrise.strftime('%H:%M')} | Naplemente: {sunset.strftime('%H:%M')}",
             font=("Arial", 10), bg='#f4e7da').pack()
    tk.Label(sun_frame, 
             text=f"Koordináták: {latitude:.4f}° É, {longitude:.4f}° K | Időzóna: {TIMEZONE}",
             font=("Arial", 9), bg='#f4e7da').pack()

    # Színes gombok 2x4 rácsban
    control_container = tk.Frame(main_frame, bg='#f4e7da')
    control_container.pack(pady=15)
    
    color_grid_frame = tk.Frame(control_container, bg='#f4e7da')
    color_grid_frame.pack(side=tk.LEFT, padx=20)
    
    for row, colors in enumerate([COLORS[:4], COLORS[4:]]):
        for col, (name, color, hex_code) in enumerate(colors):
            btn = tk.Button(
                color_grid_frame,
                text=name,
                bg=color,
                font=("Arial", 12),
                width=12,
                height=2,
                command=lambda h=hex_code: send_color_command(app, h)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)

    # Kikapcsoló gombok
    power_frame = tk.Frame(control_container, bg='#f4e7da')
    power_frame.pack(side=tk.LEFT, padx=20)

    app.power_off_btn = tk.Button(
        power_frame,
        text="Kikapcsol",
        font=("Arial", 12),
        width=12,
        height=2,
        bg="#ff6b6b",
        fg="white",
        command=lambda: turn_off_led(app)
    )
    app.power_off_btn.pack(pady=5)

    app.power_on_btn = tk.Button(
        power_frame,
        text="Bekapcsol",
        font=("Arial", 12),
        width=12,
        height=2,
        bg="#dddddd",
        command=lambda: turn_on_led(app)
    )
    app.power_on_btn.pack(pady=5)

    update_power_buttons(app)

    # Táblázat középre rendezve
    table_container = tk.Frame(main_frame, bg='#f4e7da')
    table_container.pack(pady=10)
    table_frame = tk.Frame(table_container, bg='#f4e7da')
    table_frame.pack()

    headers = ["Nap", "Szín", "Felkapcsolás", "Lekapcsolás", "Napkelte", "+perc", "Naplemente", "+perc"]
    for i, header in enumerate(headers):
        tk.Label(table_frame, text=header, font=("Arial", 10, "bold"), bg='#f4e7da').grid(row=0, column=i, padx=5, pady=2)

    app.schedule_vars = []
    app.time_comboboxes = []
    for i, day in enumerate(DAYS):
        tk.Label(table_frame, text=day, font=("Arial", 10), bg='#f4e7da').grid(row=i+1, column=0, padx=5, pady=2)

        color_var = tk.StringVar(value=app.schedule[day]["color"])
        color_cb = ttk.Combobox(table_frame, textvariable=color_var, values=[c[0] for c in COLORS], state="readonly", width=8)
        color_cb.grid(row=i+1, column=1, padx=5, pady=2)

        on_time_var = tk.StringVar(value=app.schedule[day]["on_time"])
        on_cb = ttk.Combobox(table_frame, textvariable=on_time_var, values=[f"{h:02d}:{m:02d}" for h in range(24) for m in range(60)], width=6)
        on_cb.grid(row=i+1, column=2, padx=5, pady=2)
        app.time_comboboxes.append(on_cb)

        off_time_var = tk.StringVar(value=app.schedule[day]["off_time"])
        off_cb = ttk.Combobox(table_frame, textvariable=off_time_var, values=[f"{h:02d}:{m:02d}" for h in range(24) for m in range(60)], width=6)
        off_cb.grid(row=i+1, column=3, padx=5, pady=2)
        app.time_comboboxes.append(off_cb)

        sunrise_var = tk.BooleanVar(value=app.schedule[day]["sunrise"])
        sunrise_cb = tk.Checkbutton(table_frame, variable=sunrise_var, bg='#f4e7da',
                                    command=lambda v=sunrise_var, idx=i*2: toggle_sun_time(app, v, idx))
        sunrise_cb.grid(row=i+1, column=4, padx=5)

        sunrise_offset = tk.StringVar(value=str(app.schedule[day]["sunrise_offset"]))
        tk.Entry(table_frame, textvariable=sunrise_offset, width=5).grid(row=i+1, column=5, padx=5)

        sunset_var = tk.BooleanVar(value=app.schedule[day]["sunset"])
        sunset_cb = tk.Checkbutton(table_frame, variable=sunset_var, bg='#f4e7da',
                                   command=lambda v=sunset_var, idx=i*2+1: toggle_sun_time(app, v, idx))
        sunset_cb.grid(row=i+1, column=6, padx=5)

        sunset_offset = tk.StringVar(value=str(app.schedule[day]["sunset_offset"]))
        tk.Entry(table_frame, textvariable=sunset_offset, width=5).grid(row=i+1, column=7, padx=5)

        app.schedule_vars.append({
            "day": day,
            "color": color_var,
            "on_time": on_time_var,
            "off_time": off_time_var,
            "sunrise": sunrise_var,
            "sunrise_offset": sunrise_offset,
            "sunset": sunset_var,
            "sunset_offset": sunset_offset
        })

    # Mentés/vissza gombok
    button_frame = tk.Frame(main_frame, bg='#f4e7da')
    button_frame.pack(fill=tk.X, pady=10)
    tk.Button(button_frame, text="Mentés", font=("Arial", 12), command=lambda: save_schedule(app)).pack(side=tk.RIGHT, padx=10)
    tk.Button(button_frame, text="Vissza", font=("Arial", 12), command=lambda: app.load_gui1()).pack(side=tk.LEFT, padx=10)

    update_time(app)
    check_schedule(app)

# ---- FUNKCIÓK ----
def toggle_sun_time(app, var, idx):
    combo = app.time_comboboxes[idx]
    if var.get():
        combo.configure(state='disabled')
        combo.set('')
    else:
        combo.configure(state='readonly')

def update_time(app):
    if not hasattr(app, 'time_label'):
        return
    now = datetime.now()
    magyar_nap = now.strftime('%A').capitalize()
    try:
        app.time_label.config(text=f"{now.strftime('%Y.%m.%d')} {magyar_nap} {now.strftime('%H:%M:%S')}")
        app.update_time_id = app.root.after(1000, lambda: update_time(app))
    except tk.TclError:
        pass

def update_power_buttons(app):
    if app.is_led_on:
        app.power_off_btn.config(state=tk.NORMAL, bg="#ff6b6b", fg="white")
        app.power_on_btn.config(state=tk.DISABLED, bg="#dddddd")
    else:
        app.power_off_btn.config(state=tk.DISABLED, bg="#dddddd")
        app.power_on_btn.config(state=tk.NORMAL, bg="#4CAF50", fg="white")

def send_color_command(app, hex_code):
    app.last_activity = datetime.now()
    app.last_color_hex = hex_code
    app.is_led_on = True
    update_power_buttons(app)
    asyncio.run_coroutine_threadsafe(app.ble.send_command(hex_code), app.loop)

def turn_off_led(app):
    app.is_led_on = False
    update_power_buttons(app)
    asyncio.run_coroutine_threadsafe(app.ble.send_command("7e00050300000000ef"), app.loop)

def turn_on_led(app):
    if app.last_color_hex:
        app.is_led_on = True
        update_power_buttons(app)
        asyncio.run_coroutine_threadsafe(app.ble.send_command(app.last_color_hex), app.loop)

def save_schedule(app):
    try:
        for var_set in app.schedule_vars:
            day = var_set["day"]
            app.schedule[day] = {
                "color": var_set["color"].get(),
                "on_time": var_set["on_time"].get(),
                "off_time": var_set["off_time"].get(),
                "sunrise": var_set["sunrise"].get(),
                "sunrise_offset": int(var_set["sunrise_offset"].get() or 0),
                "sunset": var_set["sunset"].get(),
                "sunset_offset": int(var_set["sunset_offset"].get() or 0)
            }

        with open(CONFIG_FILE, 'w') as f:
            json.dump(app.schedule, f, indent=4)

        messagebox.showinfo("Siker", "Az ütemezés elmentve!")
        check_schedule(app)
    except Exception as e:
        messagebox.showerror("Hiba", f"Mentési hiba: {e}")

def check_schedule(app):
    now = datetime.now()
    today = DAYS[now.weekday()]
    schedule = app.schedule.get(today, {})

    if not schedule:
        return

    latitude, longitude = get_gps_location()
    sun = Sun(latitude, longitude)
    sunrise = sun.get_local_sunrise_time(now)
    sunset = sun.get_local_sunset_time(now)

    if schedule["sunrise"]:
        on_time = sunrise + timedelta(minutes=schedule["sunrise_offset"])
        schedule["on_time"] = on_time.strftime("%H:%M")

    if schedule["sunset"]:
        off_time = sunset + timedelta(minutes=schedule["sunset_offset"])
        schedule["off_time"] = off_time.strftime("%H:%M")

    current_time = now.strftime("%H:%M")

    if schedule["on_time"] and schedule["off_time"]:
        if schedule["on_time"] <= current_time < schedule["off_time"]:
            if not app.is_led_on or app.last_color_hex != next((c[2] for c in COLORS if c[0] == schedule["color"]), ""):
                send_color_command(app, next((c[2] for c in COLORS if c[0] == schedule["color"]), ""))
        else:
            turn_off_led(app)

    app.root.after(60000, lambda: check_schedule(app))
