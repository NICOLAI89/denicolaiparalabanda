import tkinter as tk
from tkinter import ttk
from .argentum_detector import ArgentumAutoPot

class ArgentumAutoPotFrame(ttk.LabelFrame):
    """Frame de UI para configurar el Auto-Pot de Argentum."""
    
    def __init__(self, parent, on_start=None, on_stop=None):
        super().__init__(parent, text="Argentum Auto-Pot", padding=10)
        
        self.autopot = ArgentumAutoPot()
        self.on_start = on_start
        self.on_stop = on_stop
        
        self._create_widgets()
        self._setup_callbacks()
        
    def _create_widgets(self):
        # Thresholds
        ttk.Label(self, text="HP Threshold %:").grid(row=0, column=0, sticky='w')
        self.hp_threshold = ttk.Spinbox(self, from_=0, to=100, width=5)
        self.hp_threshold.set(70)
        self.hp_threshold.grid(row=0, column=1, padx=5)
        
        ttk.Label(self, text="Mana Threshold %:").grid(row=1, column=0, sticky='w')
        self.mana_threshold = ttk.Spinbox(self, from_=0, to=100, width=5)
        self.mana_threshold.set(30)
        self.mana_threshold.grid(row=1, column=1, padx=5)
        
        # Keys
        ttk.Label(self, text="HP Potion Key:").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.hp_key = ttk.Entry(self, width=5)
        self.hp_key.insert(0, '1')
        self.hp_key.grid(row=0, column=3)
        
        ttk.Label(self, text="Mana Potion Key:").grid(row=1, column=2, sticky='w', padx=(20,0))
        self.mana_key = ttk.Entry(self, width=5)
        self.mana_key.insert(0, '2')
        self.mana_key.grid(row=1, column=3)
        
        # Cooldowns
        ttk.Label(self, text="HP Cooldown (s):").grid(row=2, column=0, sticky='w')
        self.hp_cd = ttk.Spinbox(self, from_=0.5, to=10, increment=0.5, width=5)
        self.hp_cd.set(2.0)
        self.hp_cd.grid(row=2, column=1, padx=5)
        
        ttk.Label(self, text="Mana Cooldown (s):").grid(row=3, column=0, sticky='w')
        self.mana_cd = ttk.Spinbox(self, from_=0.5, to=10, increment=0.5, width=5)
        self.mana_cd.set(1.0)
        self.mana_cd.grid(row=3, column=1, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Detenido")
        ttk.Label(self, text="Status:").grid(row=4, column=0, sticky='w', pady=(10,0))
        ttk.Label(self, textvariable=self.status_var).grid(row=4, column=1, columnspan=3, sticky='w', pady=(10,0))
        
        # Botones
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=4, pady=(10,0))
        
        self.start_btn = ttk.Button(btn_frame, text="Iniciar", command=self.start)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Detener", command=self.stop, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        self.calibrate_btn = ttk.Button(btn_frame, text="Calibrar", command=self.calibrate)
        self.calibrate_btn.pack(side='left', padx=5)
        
    def _setup_callbacks(self):
        self.autopot.on_status_update = lambda s: self.status_var.set(s)
        self.autopot.on_hp_low = lambda msg: print(f"[ALERTA] {msg}")
        self.autopot.on_mana_low = lambda msg: print(f"[ALERTA] {msg}")
        
    def start(self):
        # Aplicar configuración
        self.autopot.hp_threshold = float(self.hp_threshold.get())
        self.autopot.mana_threshold = float(self.mana_threshold.get())
        self.autopot.hp_key = self.hp_key.get()
        self.autopot.mana_key = self.mana_key.get()
        self.autopot.hp_cooldown = float(self.hp_cd.get())
        self.autopot.mana_cooldown = float(self.mana_cd.get())
        
        self.autopot.start()
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        if self.on_start:
            self.on_start()
            
    def stop(self):
        self.autopot.stop()
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Detenido")
        
        if self.on_stop:
            self.on_stop()
            
    def calibrate(self):
        """Abre ventanas de calibración para ajustar las regiones."""
        self.autopot.calibrate()
        
    def get_config(self) -> dict:
        """Devuelve la configuración actual para guardar en perfil."""
        return {
            'hp_threshold': float(self.hp_threshold.get()),
            'mana_threshold': float(self.mana_threshold.get()),
            'hp_key': self.hp_key.get(),
            'mana_key': self.mana_key.get(),
            'hp_cooldown': float(self.hp_cd.get()),
            'mana_cooldown': float(self.mana_cd.get()),
        }
        
    def load_config(self, config: dict):
        """Carga configuración desde un perfil guardado."""
        self.hp_threshold.set(str(config.get('hp_threshold', 70)))
        self.mana_threshold.set(str(config.get('mana_threshold', 30)))
        self.hp_key.delete(0, 'end')
        self.hp_key.insert(0, config.get('hp_key', '1'))
        self.mana_key.delete(0, 'end')
        self.mana_key.insert(0, config.get('mana_key', '2'))
        self.hp_cd.set(str(config.get('hp_cooldown', 2.0)))
        self.mana_cd.set(str(config.get('mana_cooldown', 1.0)))