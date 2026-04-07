# Macro Tool v2 (Windows-first)

Professional modular refactor of a Tkinter macro app with profile persistence and per-macro visual detection.

## Features
- Multiple macro cards with enable/start-stop, sequence, interval, and per-macro hotkeys.
- Global input mode and specific-window mode.
- Click, right-click, double-click, and key sequence support (`u,click`, `ctrl+a`, etc).
- Persistent JSON profiles in `data/profiles` (new/load/save/save as/delete).
- Dashboard with runtime summary (status, active macros, mode, profile, target window, vision summary, detector summary).
- Vision mode per macro:
  - Template matching (best for static UI/HUD/buttons/icons).
  - ORB feature matching + homography (best for moving 2D sprites/targets with translation/scale/rotation variance).
  - Optional lightweight tracking after initial detection.
- Region selection overlay and target image capture to `data/targets`.
- Centralized logging to console + `data/logs/app.log`.

## Project Layout

```text
app/
  main.py
  ui/
    main_window.py
    macro_slot_widget.py
    dashboard.py
    theme.py
    region_selector.py
    dialogs.py
  core/
    macro_engine.py
    input_sender.py
    hotkeys.py
    window_manager.py
    state.py
    models.py
  profiles/
    profile_manager.py
  vision/
    base_detector.py
    template_matcher.py
    feature_matcher.py
    tracker.py
    detector_manager.py
    screen_capture.py
    target_manager.py
  utils/
    paths.py
    validation.py
    logger.py
    image_utils.py
    threading_utils.py
data/
  profiles/
  targets/
  logs/
main.py
requirements.txt
```

## Installation
1. Python 3.11+ recommended.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run:
   ```bash
   python main.py
   ```

## Profiles
- Profiles are JSON files under `data/profiles`.
- First run auto-creates a default profile.
- Profile stores:
  - theme/topmost/master hotkey/send mode/target window
  - per-macro standard settings
  - all vision settings (detector, target path, region, thresholds, cooldown, click+sequence behaviors, offsets, tracker options)

## Vision Workflow
1. Enable `Use visual detection` on a macro.
2. Click `Capture region` to define search area (or use full screen).
3. Click `Capture target` and draw the target patch.
4. Choose detector:
   - **template** for stable static UI elements.
   - **feature** for moving 2D targets/sprites.
5. Configure threshold, cooldown, click/sequence behavior, offsets.
6. Use `Test detection` to validate.

### Action Modes on Detection
Use checkboxes to combine behavior:
- Click only (`Click on match` on, sequence off)
- Sequence only (`Run sequence on match` on, click off)
- Sequence then click (both on)
- Click center + offset using `Offset X/Y`

## Window Mode vs Global Mode
- Detection is screen-based (full-screen or absolute region).
- In window mode, sequence sending attempts to target the selected window.
- Click-on-match is currently absolute-screen click for predictability across detector outputs.

## Extensibility (Future AI/ML)
- Detector abstraction supports pluggable detectors.
- Includes placeholder `ObjectDetectionDetector` for future YOLO/ML integration.

## Limitations
- Designed for Windows (pywin32).
- Feature matching depends on target texture quality.
- Tracker is lightweight and intentionally simple for v2 baseline.
