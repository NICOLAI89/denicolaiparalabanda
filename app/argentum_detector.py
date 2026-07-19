import cv2
import numpy as np
import mss
import time
import threading
from typing import Tuple, Optional, Callable
import keyboard

class ArgentumAutoPot:
    """
    Auto-potion system for Argentum United.
    Detects HP/Mana bars by color and sends keypresses when below threshold.
    """
    
    # Coordenadas aproximadas de las barras en la interfaz (basado en tu screenshot)
    # Estas deben calibrarse para tu resolución específica
    DEFAULT_BAR_REGIONS = {
        'hp': {'x': 1520, 'y': 890, 'w': 340, 'h': 18},      # Barra roja
        'mana': {'x': 1520, 'y': 920, 'w': 340, 'h': 18},    # Barra azul  
        'stamina': {'x': 1520, 'y': 950, 'w': 340, 'h': 18}, # Barra verde (opcional)
    }
    
    # Rangos de color en HSV para detectar las barras
    COLOR_RANGES = {
        'hp': {'low': np.array([0, 150, 100]), 'high': np.array([10, 255, 255])},      # Rojo
        'hp_alt': {'low': np.array([170, 150, 100]), 'high': np.array([180, 255, 255])}, # Rojo (wrap around)
        'mana': {'low': np.array([100, 150, 100]), 'high': np.array([130, 255, 255])},   # Azul
        'stamina': {'low': np.array([35, 150, 100]), 'high': np.array([85, 255, 255])}, # Verde/Amarillo
    }
    
    def __init__(self):
        self.sct = mss.mss()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Configuración
        self.hp_threshold = 70.0  # % de HP para usar poción
        self.mana_threshold = 30.0  # % de Mana para usar poción
        self.hp_key = '1'         # Tecla para poción de vida
        self.mana_key = '2'       # Tecla para poción de mana
        
        # Cooldowns (evitar spam)
        self.hp_cooldown = 2.0    # segundos entre pociones de vida
        self.mana_cooldown = 1.0  # segundos entre pociones de mana
        self.last_hp_pot = 0
        self.last_mana_pot = 0
        
        # Callbacks para logging/UI
        self.on_hp_low: Optional[Callable] = None
        self.on_mana_low: Optional[Callable] = None
        self.on_status_update: Optional[Callable] = None
        
        # Calibración de región (puede ajustarse)
        self.bar_regions = self.DEFAULT_BAR_REGIONS.copy()
        
    def set_region(self, bar_type: str, x: int, y: int, w: int, h: int):
        """Permite calibrar la región de detección para diferentes resoluciones."""
        self.bar_regions[bar_type] = {'x': x, 'y': y, 'w': w, 'h': h}
        
    def capture_bar_region(self, bar_type: str) -> np.ndarray:
        """Captura la región específica de la barra."""
        region = self.bar_regions[bar_type]
        screenshot = self.sct.grab(region)
        return np.array(screenshot)
    
    def get_bar_percentage(self, bar_type: str) -> float:
        """
        Analiza la barra y devuelve el porcentaje lleno (0-100).
        Usa detección de color para encontrar el ancho de la barra coloreada.
        """
        img = self.capture_bar_region(bar_type)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Crear máscara según el tipo de barra
        if bar_type == 'hp':
            mask1 = cv2.inRange(hsv, self.COLOR_RANGES['hp']['low'], self.COLOR_RANGES['hp']['high'])
            mask2 = cv2.inRange(hsv, self.COLOR_RANGES['hp_alt']['low'], self.COLOR_RANGES['hp_alt']['high'])
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            color_range = self.COLOR_RANGES.get(bar_type, self.COLOR_RANGES['mana'])
            mask = cv2.inRange(hsv, color_range['low'], color_range['high'])
        
        # Encontrar píxeles no negros en la máscara
        colored_pixels = np.sum(mask > 0)
        total_pixels = mask.shape[1] * mask.shape[0]  # ancho * alto
        
        # Calcular porcentaje
        percentage = (colored_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        
        # Método alternativo: analizar por columnas para mayor precisión
        # Encuentra la última columna con píxeles del color
        column_sums = np.sum(mask > 0, axis=0)
        filled_columns = np.sum(column_sums > 0)
        total_columns = mask.shape[1]
        percentage_alt = (filled_columns / total_columns) * 100
        
        # Promedio de ambos métodos
        return min(100.0, max(0.0, (percentage + percentage_alt) / 2))
    
    def use_potion(self, pot_type: str):
        """Simula la pulsación de tecla para usar poción."""
        current_time = time.time()
        
        if pot_type == 'hp':
            if current_time - self.last_hp_pot >= self.hp_cooldown:
                keyboard.send(self.hp_key)
                self.last_hp_pot = current_time
                if self.on_hp_low:
                    self.on_hp_low(f"HP bajo! Usando poción ({self.hp_key})")
                return True
                
        elif pot_type == 'mana':
            if current_time - self.last_mana_pot >= self.mana_cooldown:
                keyboard.send(self.mana_key)
                self.last_mana_pot = current_time
                if self.on_mana_low:
                    self.on_mana_low(f"Mana bajo! Usando poción ({self.mana_key})")
                return True
        
        return False
    
    def check_and_heal(self):
        """Loop principal de detección."""
        hp_pct = self.get_bar_percentage('hp')
        mana_pct = self.get_bar_percentage('mana')
        
        status = f"HP: {hp_pct:.1f}% | Mana: {mana_pct:.1f}%"
        if self.on_status_update:
            self.on_status_update(status)
        
        # Verificar umbrales
        if hp_pct < self.hp_threshold:
            self.use_potion('hp')
            
        if mana_pct < self.mana_threshold:
            self.use_potion('mana')
    
    def start(self):
        """Inicia el loop de detección en un thread separado."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            
    def _loop(self):
        """Loop principal del thread."""
        while self.running:
            self.check_and_heal()
            time.sleep(0.1)  # Verificar 10 veces por segundo
            
    def stop(self):
        """Detiene el auto-pot."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            
    def calibrate(self):
        """
        Modo de calibración: muestra la captura de las regiones para ajustar.
        """
        print("Modo calibración. Presiona 'q' para salir.")
        while True:
            for bar_type in ['hp', 'mana']:
                img = self.capture_bar_region(bar_type)
                cv2.imshow(f'Calibracion {bar_type.upper()}', img)
                
                # Mostrar máscara de color
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                if bar_type == 'hp':
                    mask1 = cv2.inRange(hsv, self.COLOR_RANGES['hp']['low'], self.COLOR_RANGES['hp']['high'])
                    mask2 = cv2.inRange(hsv, self.COLOR_RANGES['hp_alt']['low'], self.COLOR_RANGES['hp_alt']['high'])
                    mask = cv2.bitwise_or(mask1, mask2)
                else:
                    color_range = self.COLOR_RANGES.get(bar_type, self.COLOR_RANGES['mana'])
                    mask = cv2.inRange(hsv, color_range['low'], color_range['high'])
                
                cv2.imshow(f'Mascara {bar_type.upper()}', mask)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cv2.destroyAllWindows()


# Función de utilidad para integrar con tu sistema existente
def create_autopot_macro(profile_data: dict) -> ArgentumAutoPot:
    """
    Crea una instancia configurada desde los datos del perfil.
    """
    autopot = ArgentumAutoPot()
    
    # Cargar configuración del perfil
    if 'autopot' in profile_data:
        config = profile_data['autopot']
        autopot.hp_threshold = config.get('hp_threshold', 70.0)
        autopot.mana_threshold = config.get('mana_threshold', 30.0)
        autopot.hp_key = config.get('hp_key', '1')
        autopot.mana_key = config.get('mana_key', '2')
        autopot.hp_cooldown = config.get('hp_cooldown', 2.0)
        autopot.mana_cooldown = config.get('mana_cooldown', 1.0)
        
        # Cargar regiones personalizadas si existen
        for bar_type in ['hp', 'mana', 'stamina']:
            if f'{bar_type}_region' in config:
                autopot.set_region(bar_type, **config[f'{bar_type}_region'])
    
    return autopot