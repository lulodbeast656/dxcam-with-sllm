# --- IMPORTS ---
import dxcam
import pygetwindow as gw
import win32gui
import win32api
import win32con
import ctypes
from ctypes import wintypes
import time
from datetime import datetime
from PIL import Image
import json
import os
import threading
import glob

# --- CONFIGURAÇÕES GERAIS ---
WINDOW_SCORE_FILE = "window_scores.json"
STEAM_TITLE_FILE = "steam_titles.json"

SUPPORTED_REFRESH_RATES = [
    15, 24, 25, 30, 50, 59, 60, 65, 70, 72, 75, 85, 90,
    100, 120, 144, 165, 175, 180, 200, 240, 260, 280,
    300, 360, 390, 420, 480, 500, 540, 544
]

COMMON_SCREEN_RESOLUTIONS = [
    (800, 600), (1024, 768), (1152, 864), (1176, 664),
    (1280, 720), (1280, 768), (1280, 800), (1280, 960), (1280, 1024),
    (1360, 768), (1366, 768), (1440, 900), (1440, 1080),
    (1600, 900), (1600, 1024), (1600, 1200), (1680, 1050),
    (1920, 1080), (1920, 1200), (1920, 1440), (2048, 1536),
    (2560, 1440), (2560, 1600), (2560, 1080),
    (3440, 1440), (3840, 2160), (4096, 2160),
    (5120, 1440), (5120, 2160), (7680, 4320)
]

# --- FUNÇÕES DE ARQUIVOS E DADOS ---

def load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Erro] Falha ao carregar {path}: {e}")
        return {}

def save_json_file(data, path):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Erro] Falha ao salvar {path}: {e}")

def load_window_scores():
    return load_json_file(WINDOW_SCORE_FILE)

def save_window_scores(scores):
    save_json_file(scores, WINDOW_SCORE_FILE)

def update_window_score(title):
    scores = load_window_scores()
    scores[title] = scores.get(title, 0) + 1
    save_window_scores(scores)

def load_steam_titles():
    data = load_json_file(STEAM_TITLE_FILE)
    return set(data) if isinstance(data, list) else set()

STEAM_TITLES = load_steam_titles()

# --- UTILITÁRIOS DE MONITOR / TELA ---

def get_monitor_refresh_rate():
    class DEVMODE(ctypes.Structure):
        _fields_ = [
            ("dmDeviceName", wintypes.WCHAR * 32),
            ("dmSpecVersion", wintypes.WORD),
            ("dmDriverVersion", wintypes.WORD),
            ("dmSize", wintypes.WORD),
            ("dmDriverExtra", wintypes.WORD),
            ("dmFields", wintypes.DWORD),
            ("dmPosition", wintypes.RECT),
            ("dmDisplayOrientation", wintypes.DWORD),
            ("dmDisplayFixedOutput", wintypes.DWORD),
            ("dmColor", wintypes.SHORT), ("dmDuplex", wintypes.SHORT),
            ("dmYResolution", wintypes.SHORT), ("dmTTOption", wintypes.SHORT),
            ("dmCollate", wintypes.SHORT), ("dmFormName", wintypes.WCHAR * 32),
            ("dmLogPixels", wintypes.WORD), ("dmBitsPerPel", wintypes.DWORD),
            ("dmPelsWidth", wintypes.DWORD), ("dmPelsHeight", wintypes.DWORD),
            ("dmDisplayFlags", wintypes.DWORD), ("dmDisplayFrequency", wintypes.DWORD),
            ("dmICMMethod", wintypes.DWORD), ("dmICMIntent", wintypes.DWORD),
            ("dmMediaType", wintypes.DWORD), ("dmDitherType", wintypes.DWORD),
            ("dmReserved1", wintypes.DWORD), ("dmReserved2", wintypes.DWORD),
            ("dmPanningWidth", wintypes.DWORD), ("dmPanningHeight", wintypes.DWORD),
        ]
    devmode = DEVMODE()
    devmode.dmSize = ctypes.sizeof(DEVMODE)
    ENUM_CURRENT_SETTINGS = -1
    if ctypes.windll.user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
        return devmode.dmDisplayFrequency
    return 60

def get_supported_refresh_rate(detected, fallback=60):
    if detected in SUPPORTED_REFRESH_RATES:
        return detected
    return min(SUPPORTED_REFRESH_RATES, key=lambda x: abs(x - detected)) or fallback

def clip_region_to_screen(left, top, width, height):
    screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    right = min(left + width, screen_width)
    bottom = min(top + height, screen_height)
    return (max(0, left), max(0, top), right, bottom)

# --- SISTEMA DE INTELIGÊNCIA DE FOCO (SLLM) ---

def guess_user_focus_window():
    active_hwnd = win32gui.GetForegroundWindow()
    windows = gw.getAllWindows()
    saved_scores = load_window_scores()
    candidates = []

    for win in windows:
        if not win.visible:
            continue

        score = 0
        title = win.title.lower().strip()

        if win._hWnd == active_hwnd: score += 5
        if "game" in title or "steam" in title: score += 4
        if "editor" in title or "code" in title or "notepad" in title: score += 3
        if "chrome" in title or "browser" in title or "edge" in title: score += 2
        if "discord" in title or "chat" in title or "messenger" in title: score += 1
        if "obs" in title or "capture" in title: score -= 10
        if title in STEAM_TITLES: score += 3

        score += saved_scores.get(title, 0)
        candidates.append((score, win))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    top_score, best_window = candidates[0]
    print(f"SLLM escolheu: {best_window.title} (score total: {top_score})")
    return best_window

# --- SISTEMA DE CAPTURA ---

def save_frame(frame, prefix="captura"):
    if frame is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        Image.fromarray(frame).save(f"{prefix}_{timestamp}.png")

def delete_captures_after_delay(delay=40, prefix="captura_", extension=".png"):
    def delete_task():
        time.sleep(delay)
        files = glob.glob(f"{prefix}*{extension}")
        for f in files:
            try:
                os.remove(f)
                print(f"[AutoDelete] Arquivo removido: {f}")
            except Exception as e:
                print(f"[AutoDelete] Falha ao remover {f}: {e}")
    threading.Thread(target=delete_task, daemon=True).start()

def capture_window(window, duration=10, capture_fraction=1.0, force_refresh_rate=None):
    raw_rate = force_refresh_rate or get_monitor_refresh_rate()
    refresh_rate = get_supported_refresh_rate(raw_rate)
    capture_fps = int(refresh_rate * capture_fraction)
    interval = 1.0 / capture_fps if capture_fps > 0 else 0.033

    region = clip_region_to_screen(window.left, window.top, window.width, window.height)
    print(f"Taxa detectada: {raw_rate} Hz → Usando: {refresh_rate} Hz")
    print(f"Captura a {capture_fps} FPS | Intervalo: {interval:.3f}s")
    print(f"Região de captura: {region}")

    camera = None
    try:
        camera = dxcam.create(region=region)
        camera.start(target_fps=capture_fps)
        start_time = time.time()
        while time.time() - start_time < duration:
            frame = camera.get_latest_frame()
            save_frame(frame)
            time.sleep(interval)
        print("Captura finalizada.")
    finally:
        if camera:
            try:
                camera.stop()
            except Exception as e:
                print(f"[Aviso] Falha ao encerrar câmera: {e}")

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    print("Detectando janela em foco com SLLM adaptativo...")
    selected_window = guess_user_focus_window()

    if selected_window:
        print(f"Capturando: {selected_window.title}")
        update_window_score(selected_window.title.lower())
        delete_captures_after_delay(delay=40)
        capture_window(selected_window, duration=10, capture_fraction=1.0)
    else:
        print("Nenhuma janela válida encontrada.")
