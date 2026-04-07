# Macro Tool v2 (Windows-first)

Utilidad de escritorio para automatizar secuencias de teclado/ratón con perfiles persistentes y detección visual por macro.

## Qué hace la app
- Ejecuta macros por tarjeta (ON/OFF independiente) con secuencias tipo `ctrl+a, click, enter`.
- Soporta envío **Global** o **Ventana objetivo** (Win32) para teclas, especiales y combinaciones comunes.
- Hotkey maestro + hotkeys por macro, incluyendo ratón (`mouse4`, `mouse5`, `x1`, `x2`).
- Detección visual híbrida por macro:
  - `template` para UI estática (botones, iconos, HUD fijo).
  - `feature` (ORB + matching + homografía) para objetivos 2D en movimiento.
- Captura de región e imagen objetivo desde overlay fullscreen.
- Perfiles JSON con tema, topmost, modo, ventana objetivo y configuración completa de macros.
- Interfaz con scroll vertical, modo claro/oscuro y tooltips contextuales en español.

## Instalación
```bash
pip install -r requirements.txt
```

## Ejecución
```bash
python main.py
```

## Dependencias
Se instalan desde `requirements.txt`:
- keyboard
- pynput
- pywin32
- opencv-python
- mss
- pillow
- numpy

## Gestión de perfiles
- Crear, cargar, guardar, guardar como y borrar desde la barra superior.
- Primer inicio: se crea perfil `default` automáticamente.
- Persistencia incluye:
  - tema (light/dark)
  - topmost
  - hotkey maestro
  - modo de envío
  - etiqueta de ventana objetivo
  - configuración completa de cada macro (incluyendo visión)
- Si una ventana guardada ya no existe, se usa fallback seguro (primera visible o vacío).

## Modos de envío: Global vs Ventana
- **Global**: usa eventos globales del sistema.
- **Ventana**: intenta enviar teclas y combinaciones por Win32 al HWND seleccionado.
- Clicks en detección visual usan coordenadas de pantalla y conversión a cliente en modo Ventana.

## Hotkeys (incluye ratón)
- Hotkey maestro: inicia/detiene todas las macros.
- Hotkey por macro: inicia/detiene solo esa macro.
- Alias soportados para botones laterales:
  - `mouse4` / `x1`
  - `mouse5` / `x2`

## Flujo de detección visual
En cada macro:
1. Activa **Usar detección visual**.
2. **Capturar región** (opcional, mejora rendimiento).
3. **Capturar imagen objetivo**.
4. Elige detector:
   - `template`: objetivo estable.
   - `feature`: objetivo 2D móvil.
5. Ajusta umbral, cooldown, offset y acciones al detectar.
6. Pulsa **Probar detección**.

### Cuándo usar Template vs Feature
- Usa **Template** si el elemento casi no cambia de tamaño/rotación y siempre se ve igual.
- Usa **Feature** si el sprite/objetivo se mueve mucho o puede variar algo en escala/orientación.

## Región e imagen objetivo
- Overlay fullscreen semitransparente con selección por arrastre.
- Eventos usados: `<ButtonPress-1>`, `<B1-Motion>`, `<ButtonRelease-1>`.
- Cancelar con `Escape`.

## UI y experiencia
- Dashboard de estado en tiempo real.
- Scroll vertical visible para tarjetas.
- Tema claro/oscuro persistente por perfil.
- Tooltips de ayuda en español en áreas clave (dashboard, perfiles, modo de envío, ventana, hotkeys, controles de visión, etc.).

## Limitaciones (Windows)
- El envío a ventana depende de cómo procese mensajes cada app destino (algunas apps/juegos ignoran parte de Win32 messages).
- En targets con poca textura, `feature` puede rendir peor.
- La detección visual trabaja sobre captura de pantalla; si la ventana está oculta/minimizada, no habrá match fiable.
