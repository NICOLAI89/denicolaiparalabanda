import tkinter as tk
from tkinter import ttk
import threading
import time
import keyboard
from pynput import mouse, keyboard as pynput_keyboard
from pynput.mouse import Controller

# Windows-specific
import win32gui
import win32con
import win32api
import win32process



# =========================
# Tema global
# =========================
DARK_THEME = {
    "bg": "#1e1e1e",
    "panel": "#252526",
    "panel2": "#2d2d30",
    "fg": "#ffffff",
    "entry_bg": "#1a1a1a",
    "entry_fg": "#ffffff",
    "button_bg": "#3a3a3a",
    "button_fg": "#ffffff",
    "status_on_fg": "#7CFC90",
    "status_off_fg": "#ff6b6b",
    "macro_on_bg": "#1f3524",
    "macro_off_bg": "#252526",
    "macro_btn_on": "#39b54a",
    "macro_btn_off": "#d64545",
}

LIGHT_THEME = {
    "bg": "#f0f0f0",
    "panel": "#f6f6f6",
    "panel2": "#ffffff",
    "fg": "#000000",
    "entry_bg": "#ffffff",
    "entry_fg": "#000000",
    "button_bg": "#e0e0e0",
    "button_fg": "#000000",
    "status_on_fg": "#0f6b0f",
    "status_off_fg": "#b00020",
    "macro_on_bg": "#d8ffd8",
    "macro_off_bg": "#f3f3f3",
    "macro_btn_on": "#39b54a",
    "macro_btn_off": "#d64545",
}

current_theme = LIGHT_THEME


# =========================
# Estado global
# =========================
master_running = False
last_toggle_time = 0
TOGGLE_DEBOUNCE = 0.25
mouse_controller = Controller()

mouse_listener = None
keyboard_listener = None

master_hotkey = None
macro_slots = []

window_map = {}  # "Título" -> hwnd
capture_pending_slot = None
capture_pending_hwnd = None

# =========================
# Utilidades hotkeys
# =========================
def parse_mouse_hotkey(value: str):
    value = value.strip().lower()
    mapping = {
        "mouse4": mouse.Button.x1,
        "x1": mouse.Button.x1,
        "button.x1": mouse.Button.x1,
        "mouse5": mouse.Button.x2,
        "x2": mouse.Button.x2,
        "button.x2": mouse.Button.x2,
    }
    return mapping.get(value)


def normalize_hotkey(value: str):
    value = value.strip().lower()
    mouse_key = parse_mouse_hotkey(value)
    if mouse_key is not None:
        return mouse_key
    return value if value else None


def pynput_key_to_string(key):
    try:
        if hasattr(key, "char") and key.char:
            return key.char.lower()
    except Exception:
        pass

    special_map = {
        pynput_keyboard.Key.f1: "f1",
        pynput_keyboard.Key.f2: "f2",
        pynput_keyboard.Key.f3: "f3",
        pynput_keyboard.Key.f4: "f4",
        pynput_keyboard.Key.f5: "f5",
        pynput_keyboard.Key.f6: "f6",
        pynput_keyboard.Key.f7: "f7",
        pynput_keyboard.Key.f8: "f8",
        pynput_keyboard.Key.f9: "f9",
        pynput_keyboard.Key.f10: "f10",
        pynput_keyboard.Key.f11: "f11",
        pynput_keyboard.Key.f12: "f12",
        pynput_keyboard.Key.esc: "esc",
        pynput_keyboard.Key.space: "space",
        pynput_keyboard.Key.enter: "enter",
        pynput_keyboard.Key.tab: "tab",
        pynput_keyboard.Key.shift: "shift",
        pynput_keyboard.Key.shift_r: "right shift",
        pynput_keyboard.Key.ctrl: "ctrl",
        pynput_keyboard.Key.ctrl_r: "right ctrl",
        pynput_keyboard.Key.alt: "alt",
        pynput_keyboard.Key.alt_r: "right alt",
    }
    return special_map.get(key, str(key).replace("Key.", "").lower())


# =========================
# Helpers UI
# =========================
def set_status(text):
    status_label.config(text=text)


def update_master_running_state():
    global master_running
    master_running = any(slot.running for slot in macro_slots)


def toggle_theme():
    global current_theme
    current_theme = DARK_THEME if current_theme == LIGHT_THEME else LIGHT_THEME
    apply_theme()


# =========================
# Ventanas destino
# =========================
def enum_visible_windows():
    windows = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        if win32gui.IsIconic(hwnd):
            return

        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return

        # Filtrar ventanas muy "vacías" o de sistema
        class_name = win32gui.GetClassName(hwnd)
        if class_name in {"Shell_TrayWnd", "Progman", "WorkerW"}:
            return

        windows.append((title, hwnd))

    win32gui.EnumWindows(callback, None)
    windows.sort(key=lambda x: x[0].lower())
    return windows


def refresh_window_list():
    global window_map
    items = enum_visible_windows()

    window_map = {}
    titles = []
    for title, hwnd in items:
        display = f"{title}  [HWND {hwnd}]"
        window_map[display] = hwnd
        titles.append(display)

    target_window_combo["values"] = titles

    if titles:
        current = target_window_var.get().strip()
        if current not in window_map:
            target_window_var.set(titles[0])
    else:
        target_window_var.set("")

    update_target_window_status()


def get_selected_hwnd():
    display = target_window_var.get().strip()
    return window_map.get(display)

def find_child_windows(parent_hwnd):
    children = []

    def callback(hwnd, _):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
            children.append(hwnd)

    try:
        win32gui.EnumChildWindows(parent_hwnd, callback, None)
    except Exception:
        pass

    return children


def get_best_text_hwnd(parent_hwnd):
    """
    Intenta encontrar el mejor HWND para texto.
    Prioridad:
    - control con foco dentro del hilo de la ventana
    - clases típicas de edición
    - fallback a la ventana principal
    """
    if not parent_hwnd or not win32gui.IsWindow(parent_hwnd):
        return parent_hwnd


    # 1) intentar control con foco del mismo hilo
    try:
        target_thread, _ = win32process.GetWindowThreadProcessId(parent_hwnd)
        gui = win32gui.GetGUIThreadInfo(target_thread)
        focus_hwnd = gui.get("hwndFocus")
        if focus_hwnd and win32gui.IsWindow(focus_hwnd):
            return focus_hwnd
    except Exception:
        pass

    # 2) buscar hijos conocidos de texto
    preferred_classes = {
        "Edit",
        "RichEdit20A",
        "RichEdit20W",
        "RICHEDIT50W",
        "Scintilla",
        "NotepadTextBox",
    }

    for child in find_child_windows(parent_hwnd):
        try:
            cls = win32gui.GetClassName(child)
            if cls in preferred_classes:
                return child
        except Exception:
            pass

    # 3) fallback
    return parent_hwnd


def update_target_window_status():
    if send_mode_var.get() == "global":
        target_window_status.config(text="Destino actual: input global del sistema")
        return

    hwnd = get_selected_hwnd()
    if hwnd and win32gui.IsWindow(hwnd):
        title = win32gui.GetWindowText(hwnd)
        target_window_status.config(text=f"Destino actual: {title} (HWND {hwnd})")
    else:
        target_window_status.config(text="Destino actual: ventana no válida / no seleccionada")


# =========================
# Input helpers
# =========================
SPECIAL_KEYS = {
    "space": win32con.VK_SPACE,
    "enter": win32con.VK_RETURN,
    "tab": win32con.VK_TAB,
    "esc": win32con.VK_ESCAPE,
    "escape": win32con.VK_ESCAPE,
    "backspace": win32con.VK_BACK,
    "delete": win32con.VK_DELETE,
    "insert": win32con.VK_INSERT,
    "home": win32con.VK_HOME,
    "end": win32con.VK_END,
    "pageup": win32con.VK_PRIOR,
    "pagedown": win32con.VK_NEXT,
    "left": win32con.VK_LEFT,
    "right": win32con.VK_RIGHT,
    "up": win32con.VK_UP,
    "down": win32con.VK_DOWN,
    "f1": win32con.VK_F1,
    "f2": win32con.VK_F2,
    "f3": win32con.VK_F3,
    "f4": win32con.VK_F4,
    "f5": win32con.VK_F5,
    "f6": win32con.VK_F6,
    "f7": win32con.VK_F7,
    "f8": win32con.VK_F8,
    "f9": win32con.VK_F9,
    "f10": win32con.VK_F10,
    "f11": win32con.VK_F11,
    "f12": win32con.VK_F12,
}

MOD_KEYS = {
    "ctrl": win32con.VK_CONTROL,
    "control": win32con.VK_CONTROL,
    "shift": win32con.VK_SHIFT,
    "alt": win32con.VK_MENU,
}


def make_lparam(x, y):
    return win32api.MAKELONG(x, y)


def get_vk_for_key(key_name: str):
    key_name = key_name.strip().lower()

    if key_name in SPECIAL_KEYS:
        return SPECIAL_KEYS[key_name]

    if len(key_name) == 1:
        vk = win32api.VkKeyScan(key_name)
        if vk == -1:
            return None
        return vk & 0xFF

    return None


def post_keydown(hwnd, vk):
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)


def post_keyup(hwnd, vk):
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)

def send_key_to_window(hwnd, key_expr: str):
    """
    Soporta:
    - a
    - space
    - enter
    - f1...f12
    - ctrl+a
    - shift+a
    - alt+a
    - ctrl+shift+a
    """

    target_hwnd = get_best_text_hwnd(hwnd)

    parts = [p.strip().lower() for p in key_expr.split("+") if p.strip()]
    if not parts:
        return

    mods = parts[:-1]
    main = parts[-1]

    mod_vks = []
    for mod in mods:
        vk = MOD_KEYS.get(mod)
        if vk is None:
            raise ValueError(f"Modificador no soportado en modo ventana: {mod}")
        mod_vks.append(vk)

    main_vk = get_vk_for_key(main)
    if main_vk is None:
        raise ValueError(f"Tecla no soportada en modo ventana: {main}")

    # CASO 1: texto simple -> usar WM_CHAR directo
    if len(main) == 1 and not mod_vks:
        win32gui.SendMessage(target_hwnd, win32con.WM_CHAR, ord(main), 0)
        return

    # CASO 2: teclas especiales o combinaciones
    for vk in mod_vks:
        win32api.PostMessage(target_hwnd, win32con.WM_KEYDOWN, vk, 0)
        time.sleep(0.01)

    win32api.PostMessage(target_hwnd, win32con.WM_KEYDOWN, main_vk, 0)
    time.sleep(0.02)

    # Para texto con shift/ctrl/alt no mandamos WM_CHAR directo
    win32api.PostMessage(target_hwnd, win32con.WM_KEYUP, main_vk, 0)
    time.sleep(0.01)

    for vk in reversed(mod_vks):
        win32api.PostMessage(target_hwnd, win32con.WM_KEYUP, vk, 0)
        time.sleep(0.01)

def send_click_to_window(hwnd, x, y, button_type="left", double=False):
    lparam = make_lparam(x, y)

    win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
    time.sleep(0.01)

    if button_type == "left":
        down_msg = win32con.WM_LBUTTONDOWN
        up_msg = win32con.WM_LBUTTONUP
        wparam_down = win32con.MK_LBUTTON
    elif button_type == "right":
        down_msg = win32con.WM_RBUTTONDOWN
        up_msg = win32con.WM_RBUTTONUP
        wparam_down = win32con.MK_RBUTTON
    else:
        raise ValueError("button_type inválido")

    count = 2 if double else 1
    for _ in range(count):
        win32api.PostMessage(hwnd, down_msg, wparam_down, lparam)
        time.sleep(0.01)
        win32api.PostMessage(hwnd, up_msg, 0, lparam)
        time.sleep(0.03)


def send_action_global(action: str):
    action = action.strip().lower()

    if action == "click":
        mouse_controller.click(mouse.Button.left, 1)
    elif action == "rightclick":
        mouse_controller.click(mouse.Button.right, 1)
    elif action == "doubleclick":
        mouse_controller.click(mouse.Button.left, 2)
    else:
        keyboard.send(action)


def send_action_window(hwnd, action: str, click_point=None):
    action = action.strip().lower()

    if action in {"click", "rightclick", "doubleclick"}:
        if click_point is None:
            raise ValueError("No hay punto de click capturado para este macro")

        x, y = click_point
        if action == "click":
            send_click_to_window(hwnd, x, y, button_type="left", double=False)
        elif action == "rightclick":
            send_click_to_window(hwnd, x, y, button_type="right", double=False)
        elif action == "doubleclick":
            send_click_to_window(hwnd, x, y, button_type="left", double=True)
    else:
        send_key_to_window(hwnd, action)


def parse_sequence(raw: str):
    """
    Permite:
    - x
    - ctrl+a
    - click
    - x,click
    - x,rightclick
    - x,doubleclick
    """
    raw = raw.strip().lower()
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def execute_sequence(raw: str, mode: str, hwnd=None, click_point=None):
    actions = parse_sequence(raw)

    for idx, action in enumerate(actions):
        if mode == "global":
            send_action_global(action)
        else:
            if hwnd is None or not win32gui.IsWindow(hwnd):
                raise ValueError("Ventana destino inválida")
            send_action_window(hwnd, action, click_point=click_point)

        # pequeña pausa entre partes de la secuencia
        if idx < len(actions) - 1:
            time.sleep(0.03)


# =========================
# Clase Macro individual
# =========================
class MacroSlot:
    def __init__(self, parent, index):
        self.index = index
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.individual_hotkey = None
        self.click_point = None  # coordenadas cliente para ventana específica

        self.enabled_var = tk.BooleanVar(value=False)

        self.frame = tk.LabelFrame(
            parent,
            text=f"Macro {index} [OFF]",
            padx=8,
            pady=8,
            bd=2,
            relief="groove",
        )
        self.frame.pack(fill="x", padx=10, pady=6)

        self.state_label = tk.Label(
            self.frame,
            text="● OFF",
            font=("Arial", 12, "bold"),
        )
        self.state_label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.power_btn = tk.Button(
            self.frame,
            text="ENCENDER MACRO",
            font=("Arial", 10, "bold"),
            fg="white",
            activeforeground="white",
            command=self.toggle
        )
        self.power_btn.grid(row=0, column=1, sticky="e", padx=(8, 0), pady=(0, 6))

        self.enable_chk = tk.Checkbutton(
            self.frame,
            text="Activar",
            variable=self.enabled_var,
        )
        self.enable_chk.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.key_label = tk.Label(
            self.frame,
            text="Tecla / secuencia (ej: 1, space, ctrl+a, click, u,click)"
        )
        self.key_label.grid(row=2, column=0, columnspan=2, sticky="w")

        self.key_entry = tk.Entry(self.frame)
        self.key_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        self.interval_label = tk.Label(
            self.frame,
            text="Intervalo (ms)"
        )
        self.interval_label.grid(row=4, column=0, columnspan=2, sticky="w")

        self.interval_entry = tk.Entry(self.frame)
        self.interval_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        self.hotkey_label = tk.Label(
            self.frame,
            text="Hotkey individual (opcional: f7, mouse4, mouse5)"
        )
        self.hotkey_label.grid(row=6, column=0, columnspan=2, sticky="w")

        self.toggle_entry = tk.Entry(self.frame)
        self.toggle_entry.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        self.toggle_btn = tk.Button(
            self.frame,
            text="Definir hotkey individual",
            command=self.set_individual_hotkey
        )
        self.toggle_btn.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        self.toggle_status = tk.Label(
            self.frame,
            text="Hotkey individual: no definida"
        )
        self.toggle_status.grid(row=9, column=0, columnspan=2, sticky="w")

        self.capture_btn = tk.Button(
            self.frame,
            text="Capturar punto de click",
            command=self.capture_click_point
        )
        self.capture_btn.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(8, 4))

        self.capture_status = tk.Label(
            self.frame,
            text="Punto click: no capturado"
        )
        self.capture_status.grid(row=11, column=0, columnspan=2, sticky="w")

        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        self.apply_visual_state()

    def apply_visual_state(self):
        theme = current_theme
        is_on = self.running
        bg = theme["macro_on_bg"] if is_on else theme["macro_off_bg"]

        self.frame.config(
            text=f"Macro {self.index} [{'ON' if is_on else 'OFF'}]",
            bg=bg,
            fg=theme["fg"]
        )

        self.state_label.config(
            text="● ON" if is_on else "● OFF",
            fg=theme["status_on_fg"] if is_on else theme["status_off_fg"],
            bg=bg
        )

        self.power_btn.config(
            text="APAGAR MACRO" if is_on else "ENCENDER MACRO",
            bg=theme["macro_btn_off"] if is_on else theme["macro_btn_on"],
            fg="white",
            activebackground=theme["macro_btn_off"] if is_on else theme["macro_btn_on"],
            activeforeground="white"
        )

        self.enable_chk.config(
            bg=bg,
            fg=theme["fg"],
            activebackground=bg,
            activeforeground=theme["fg"],
            selectcolor=theme["entry_bg"]
        )

        for widget in [
            self.key_label,
            self.interval_label,
            self.hotkey_label,
            self.toggle_status,
            self.capture_status,
        ]:
            widget.config(bg=bg, fg=theme["fg"])

        for entry in [self.key_entry, self.interval_entry, self.toggle_entry]:
            entry.config(
                bg=theme["entry_bg"],
                fg=theme["entry_fg"],
                insertbackground=theme["entry_fg"]
            )

        for btn in [self.toggle_btn, self.capture_btn]:
            btn.config(
                bg=theme["button_bg"],
                fg=theme["button_fg"],
                activebackground=theme["button_bg"],
                activeforeground=theme["button_fg"]
            )

    def get_key(self):
        return self.key_entry.get().strip()

    def get_interval(self):
        raw = self.interval_entry.get().strip()
        interval = int(raw)
        if interval <= 0:
            raise ValueError
        return interval

    def uses_click(self):
        raw = self.get_key().lower()
        return any(part.strip() in {"click", "rightclick", "doubleclick"} for part in raw.split(","))

    def validate(self):
        if not self.enabled_var.get():
            return False, f"Macro {self.index}: desactivada"

        key = self.get_key()
        if not key:
            return False, f"Macro {self.index}: tecla inválida"

        try:
            self.get_interval()
        except ValueError:
            return False, f"Macro {self.index}: intervalo inválido"

        if send_mode_var.get() == "window":
            hwnd = get_selected_hwnd()
            if not hwnd or not win32gui.IsWindow(hwnd):
                return False, f"Macro {self.index}: ventana destino inválida"

            if self.uses_click() and self.click_point is None:
                return False, f"Macro {self.index}: capturá un punto de click"

        return True, ""

    def capture_click_point(self):
        global capture_pending_slot, capture_pending_hwnd

        hwnd = get_selected_hwnd()
        if send_mode_var.get() != "window":
            self.capture_status.config(text="Punto click: solo aplica en modo ventana")
            set_status("Poné modo: Ventana específica para capturar punto")
            return

        if not hwnd or not win32gui.IsWindow(hwnd):
            self.capture_status.config(text="Punto click: ventana inválida")
            set_status("Seleccioná una ventana válida primero")
            return

        capture_pending_slot = self
        capture_pending_hwnd = hwnd

        self.capture_status.config(text="Punto click: esperando tu próximo click...")
        set_status(f"Macro {self.index}: hacé click en el lugar que querés capturar")

    def macro_loop(self):
        key = self.get_key().strip().lower()
        interval = self.get_interval()

        while not self.stop_event.is_set():
            try:
                mode = send_mode_var.get()

                if mode == "global":
                    execute_sequence(key, mode="global")
                else:
                    hwnd = get_selected_hwnd()
                    execute_sequence(
                        key,
                        mode="window",
                        hwnd=hwnd,
                        click_point=self.click_point
                    )

            except Exception as e:
                print(f"Error Macro {self.index} enviando '{key}': {e}")
                set_status(f"Macro {self.index}: error: {e}")
                self.stop()
                break

            time.sleep(interval / 1000.0)

    def start(self):
        if self.running:
            return

        ok, msg = self.validate()
        if not ok:
            set_status(msg)
            return

        self.stop_event.clear()
        self.thread = threading.Thread(target=self.macro_loop, daemon=True)
        self.thread.start()
        self.running = True
        self.apply_visual_state()
        set_status(f"Status: Macro {self.index} FUNCIONANDO")

    def stop(self):
        if not self.running:
            return

        self.stop_event.set()
        self.running = False
        self.apply_visual_state()
        set_status(f"Status: Macro {self.index} DETENIDA")

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

        update_master_running_state()

    def set_individual_hotkey(self):
        raw = self.toggle_entry.get().strip().lower()
        hk = normalize_hotkey(raw)
        if hk is None:
            self.toggle_status.config(text="Hotkey individual inválida")
            return

        self.individual_hotkey = hk
        self.toggle_status.config(text=f"Hotkey individual: {raw}")


# =========================
# Toggle general
# =========================
def toggle_all_macros():
    global master_running, last_toggle_time

    now = time.time()
    if now - last_toggle_time < TOGGLE_DEBOUNCE:
        return
    last_toggle_time = now

    if not master_running:
        found_valid = False
        for slot in macro_slots:
            if slot.enabled_var.get():
                slot.start()
                if slot.running:
                    found_valid = True

        if found_valid:
            master_running = True
            set_status("Status: TODAS/VARIAS FUNCIONANDO")
        else:
            set_status("Status: No hay macros válidas activadas")
    else:
        for slot in macro_slots:
            slot.stop()
        master_running = False
        set_status("Status: TODAS DETENIDAS")

    update_master_running_state()


def set_master_hotkey():
    global master_hotkey
    raw = master_toggle_entry.get().strip().lower()
    hk = normalize_hotkey(raw)
    if hk is None:
        master_toggle_status.config(text="Hotkey general inválida")
        return

    master_hotkey = hk
    master_toggle_status.config(text=f"Hotkey general: {raw}")


# =========================
# Listeners
# =========================
def on_mouse_click(x, y, button, pressed):
    global capture_pending_slot, capture_pending_hwnd

# Captura de punto pendiente
    if capture_pending_slot is not None and button == mouse.Button.left:
        try:
            hwnd = capture_pending_hwnd

            if hwnd and win32gui.IsWindow(hwnd):
                x_client, y_client = win32gui.ScreenToClient(hwnd, (x, y))
                capture_pending_slot.click_point = (x_client, y_client)
                capture_pending_slot.capture_status.config(
                    text=f"Punto click: x={x_client}, y={y_client}"
                )
                set_status(
                    f"Macro {capture_pending_slot.index}: punto capturado x={x_client}, y={y_client}"
                )
            else:
                capture_pending_slot.capture_status.config(
                    text="Punto click: ventana inválida al capturar"
                )
                set_status("Error: la ventana seleccionada ya no es válida")

        except Exception as e:
            capture_pending_slot.capture_status.config(
                text="Punto click: error al capturar"
            )
            set_status(f"Error capturando punto: {e}")

        capture_pending_slot = None
        capture_pending_hwnd = None
        return

    global master_hotkey

    if isinstance(master_hotkey, mouse.Button) and button == master_hotkey:
        toggle_all_macros()
        update_master_running_state()
        return

    for slot in macro_slots:
        if isinstance(slot.individual_hotkey, mouse.Button) and button == slot.individual_hotkey:
            slot.toggle()
            update_master_running_state()
            return


def on_key_press(key):
    pressed = pynput_key_to_string(key)

    global master_hotkey
    if isinstance(master_hotkey, str) and pressed == master_hotkey:
        toggle_all_macros()
        update_master_running_state()
        return

    for slot in macro_slots:
        if isinstance(slot.individual_hotkey, str) and pressed == slot.individual_hotkey:
            slot.toggle()
            update_master_running_state()
            return


def start_listeners():
    global mouse_listener, keyboard_listener

    if mouse_listener is None:
        mouse_listener = mouse.Listener(on_click=on_mouse_click)
        mouse_listener.daemon = True
        mouse_listener.start()

    if keyboard_listener is None:
        keyboard_listener = pynput_keyboard.Listener(on_press=on_key_press)
        keyboard_listener.daemon = True
        keyboard_listener.start()


# =========================
# Ventana al frente
# =========================
def on_minimize(event=None):
    if root.state() == "iconic":
        root.attributes("-topmost", False)


def on_restore(event=None):
    if root.state() != "iconic" and keep_on_top_var.get():
        root.attributes("-topmost", True)


def apply_topmost():
    if root.state() == "iconic":
        root.attributes("-topmost", False)
    else:
        root.attributes("-topmost", keep_on_top_var.get())


def on_close():
    for slot in macro_slots:
        slot.stop()
    root.destroy()


# =========================
# Scroll
# =========================
def _on_canvas_configure(event):
    canvas.itemconfig(canvas_window, width=event.width)


def _on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))


def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# =========================
# Tema
# =========================
def apply_theme():
    theme = current_theme

    root.configure(bg=theme["bg"])
    outer.configure(bg=theme["bg"])
    canvas.configure(bg=theme["bg"])
    scrollable_frame.configure(bg=theme["bg"])
    top_frame.configure(bg=theme["bg"])
    bottom.configure(bg=theme["bg"])

    theme_btn.config(
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["button_bg"],
        activeforeground=theme["button_fg"]
    )

    master_hotkey_label.config(bg=theme["bg"], fg=theme["fg"])
    master_toggle_entry.config(
        bg=theme["entry_bg"],
        fg=theme["entry_fg"],
        insertbackground=theme["entry_fg"]
    )
    master_toggle_btn.config(
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["button_bg"],
        activeforeground=theme["button_fg"]
    )
    master_toggle_status.config(bg=theme["bg"], fg=theme["fg"])

    send_mode_label.config(bg=theme["bg"], fg=theme["fg"])
    mode_global_rb.config(
        bg=theme["bg"], fg=theme["fg"],
        activebackground=theme["bg"], activeforeground=theme["fg"],
        selectcolor=theme["entry_bg"]
    )
    mode_window_rb.config(
        bg=theme["bg"], fg=theme["fg"],
        activebackground=theme["bg"], activeforeground=theme["fg"],
        selectcolor=theme["entry_bg"]
    )

    target_window_label.config(bg=theme["bg"], fg=theme["fg"])
    refresh_windows_btn.config(
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["button_bg"],
        activeforeground=theme["button_fg"]
    )
    target_window_status.config(bg=theme["bg"], fg=theme["fg"])

    keep_on_top_chk.config(
        bg=theme["bg"],
        fg=theme["fg"],
        activebackground=theme["bg"],
        activeforeground=theme["fg"],
        selectcolor=theme["entry_bg"]
    )

    toggle_all_btn.config(
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["button_bg"],
        activeforeground=theme["button_fg"]
    )

    status_label.config(bg=theme["bg"], fg=theme["fg"])
    help_label.config(bg=theme["bg"], fg=theme["fg"])

    for slot in macro_slots:
        slot.apply_visual_state()


def on_send_mode_changed():
    update_target_window_status()
    if send_mode_var.get() == "window":
        set_status("Modo actual: ventana específica")
    else:
        set_status("Modo actual: input global del sistema")


# =========================
# UI
# =========================
root = tk.Tk()
root.title("DE NICOLAI PARA LA BANDA")
root.geometry("560x900")
root.minsize(520, 600)

outer = tk.Frame(root)
outer.pack(fill="both", expand=True)

canvas = tk.Canvas(outer, highlightthickness=0)
scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind("<Configure>", _on_frame_configure)
canvas.bind("<Configure>", _on_canvas_configure)

canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Top frame
top_frame = tk.Frame(scrollable_frame, padx=10, pady=10)
top_frame.pack(fill="x")

theme_btn = tk.Button(
    top_frame,
    text="🌙 Cambiar tema",
    command=toggle_theme
)
theme_btn.pack(fill="x", pady=(0, 8))

master_hotkey_label = tk.Label(
    top_frame,
    text="Hotkey general (activa/desactiva varias a la vez: f6, mouse4, mouse5)"
)
master_hotkey_label.pack(anchor="w")

master_toggle_entry = tk.Entry(top_frame)
master_toggle_entry.insert(0, "f6")
master_toggle_entry.pack(fill="x", pady=(0, 6))

master_toggle_btn = tk.Button(top_frame, text="Definir hotkey general", command=set_master_hotkey)
master_toggle_btn.pack(fill="x")

master_toggle_status = tk.Label(top_frame, text="Hotkey general: no definida")
master_toggle_status.pack(anchor="w", pady=(6, 8))

send_mode_var = tk.StringVar(value="global")

send_mode_label = tk.Label(top_frame, text="Modo de envío")
send_mode_label.pack(anchor="w")

mode_frame = tk.Frame(top_frame)
mode_frame.pack(fill="x", pady=(0, 6))

mode_global_rb = tk.Radiobutton(
    mode_frame,
    text="Global del sistema",
    variable=send_mode_var,
    value="global",
    command=on_send_mode_changed
)
mode_global_rb.pack(side="left", padx=(0, 10))

mode_window_rb = tk.Radiobutton(
    mode_frame,
    text="Ventana específica",
    variable=send_mode_var,
    value="window",
    command=on_send_mode_changed
)
mode_window_rb.pack(side="left")

target_window_label = tk.Label(
    top_frame,
    text="Selector ventana destino"
)
target_window_label.pack(anchor="w")

target_window_var = tk.StringVar()
target_window_combo = ttk.Combobox(
    top_frame,
    textvariable=target_window_var,
    state="readonly"
)
target_window_combo.pack(fill="x", pady=(0, 6))
target_window_combo.bind("<<ComboboxSelected>>", lambda e: update_target_window_status())

refresh_windows_btn = tk.Button(
    top_frame,
    text="Refrescar lista de ventanas",
    command=refresh_window_list
)
refresh_windows_btn.pack(fill="x")

target_window_status = tk.Label(top_frame, text="Destino actual: input global del sistema")
target_window_status.pack(anchor="w", pady=(6, 0))

keep_on_top_var = tk.BooleanVar(value=True)
keep_on_top_chk = tk.Checkbutton(
    top_frame,
    text="Mantener ventana al frente salvo minimizada",
    variable=keep_on_top_var,
    command=apply_topmost
)
keep_on_top_chk.pack(anchor="w", pady=(8, 0))

ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", padx=10, pady=6)

# Macros
macro_slots = [MacroSlot(scrollable_frame, 1), MacroSlot(scrollable_frame, 2), MacroSlot(scrollable_frame, 3)]

# Defaults
macro_slots[0].key_entry.insert(0, "l")
macro_slots[0].interval_entry.insert(0, "25")
macro_slots[0].toggle_entry.insert(0, "1")

macro_slots[1].key_entry.insert(0, "i")
macro_slots[1].interval_entry.insert(0, "25")
macro_slots[1].toggle_entry.insert(0, "2")

macro_slots[2].key_entry.insert(0, "u,click")
macro_slots[2].interval_entry.insert(0, "25")
macro_slots[2].toggle_entry.insert(0, "8")

bottom = tk.Frame(scrollable_frame, padx=10, pady=10)
bottom.pack(fill="x")

toggle_all_btn = tk.Button(
    bottom,
    text="Activar / Desactivar TODAS",
    command=lambda: [toggle_all_macros(), update_master_running_state()]
)
toggle_all_btn.pack(fill="x")

status_label = tk.Label(bottom, text="Status: DETENIDO", font=("Arial", 11, "bold"))
status_label.pack(pady=10)

help_label = tk.Label(
    bottom,
    text=(
        "Modo global:\n"
        "- usa keyboard/pynput sobre la ventana con foco\n\n"
        "Modo ventana específica:\n"
        "- elegís la ventana en el selector\n"
        "- si el macro usa click/rightclick/doubleclick,\n"
        "  capturá antes el punto con 'Capturar punto de click'\n\n"
        "Ejemplos key input:\n"
        "- x\n"
        "- ctrl+a\n"
        "- click\n"
        "- u,click\n"
        "- u,rightclick\n"
        "- u,doubleclick"
    ),
    justify="left"
)
help_label.pack(anchor="w")

root.attributes("-topmost", True)
root.bind("<Unmap>", on_minimize)
root.bind("<Map>", on_restore)
root.protocol("WM_DELETE_WINDOW", on_close)

start_listeners()
set_master_hotkey()
refresh_window_list()
apply_theme()
root.mainloop()
