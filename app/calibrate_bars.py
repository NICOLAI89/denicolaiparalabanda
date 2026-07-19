#!/usr/bin/env python3
"""
Script para calibrar las coordenadas de las barras de HP/Mana.
Ejecutar esto primero para obtener las coordenadas correctas para tu resolución.
"""

import cv2
import numpy as np
import mss
import json

def select_region_screenshot():
    """
    Muestra la pantalla completa y permite seleccionar una región con el mouse.
    Devuelve las coordenadas {x, y, w, h}.
    """
    sct = mss.mss()
    screenshot = np.array(sct.grab(sct.monitors[0]))
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    
    # Redimensionar si es muy grande para facilitar selección
    scale = 0.7 if screenshot.shape[1] > 1920 else 1.0
    if scale < 1.0:
        display_img = cv2.resize(screenshot, None, fx=scale, fy=scale)
    else:
        display_img = screenshot.copy()
    
    clone = display_img.copy()
    ref_point = []
    cropping = False
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal ref_point, cropping, clone
        
        if event == cv2.EVENT_LBUTTONDOWN:
            ref_point = [(x, y)]
            cropping = True
            
        elif event == cv2.EVENT_LBUTTONUP:
            ref_point.append((x, y))
            cropping = False
            
            # Dibujar rectángulo
            cv2.rectangle(clone, ref_point[0], ref_point[1], (0, 255, 0), 2)
            cv2.imshow("Selecciona la region de la barra", clone)
    
    cv2.namedWindow("Selecciona la region de la barra")
    cv2.setMouseCallback("Selecciona la region de la barra", mouse_callback)
    
    print("Instrucciones:")
    print("1. Haz clic y arrastra para seleccionar la barra")
    print("2. Presiona 'r' para reiniciar")
    print("3. Presiona 'q' para confirmar la selección")
    print()
    
    while True:
        cv2.imshow("Selecciona la region de la barra", clone)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('r'):
            clone = display_img.copy()
            ref_point = []
            
        elif key == ord('q'):
            break
    
    cv2.destroyAllWindows()
    
    if len(ref_point) == 2:
        # Convertir coordenadas de vuelta a resolución original
        x1, y1 = int(ref_point[0][0] / scale), int(ref_point[0][1] / scale)
        x2, y2 = int(ref_point[1][0] / scale), int(ref_point[1][1] / scale)
        
        return {
            'x': min(x1, x2),
            'y': min(y1, y2),
            'w': abs(x2 - x1),
            'h': abs(y2 - y1)
        }
    
    return None

def main():
    print("=== Calibración de Barras para Argentum United ===\n")
    
    regions = {}
    
    for bar_name in ['hp', 'mana']:
        input(f"Presiona Enter para seleccionar la región de la barra de {bar_name.upper()}...")
        
        region = select_region_screenshot()
        if region:
            regions[bar_name] = region
            print(f"✓ Región de {bar_name.upper()} guardada: {region}")
        else:
            print(f"✗ No se seleccionó región para {bar_name}")
    
    # Guardar configuración
    config = {'bar_regions': regions}
    with open('argentum_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n=== Configuración guardada en argentum_config.json ===")
    print(json.dumps(config, indent=2))

if __name__ == '__main__':
    main()