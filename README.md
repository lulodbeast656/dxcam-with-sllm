# dxcam-with-sllm

An intelligent screen and window capture system for Windows, powered by an adaptive prioritization module called **SLLM (Self-Learning Logic Module)**. It automatically detects the most relevant window based on intelligent heuristics and usage history, performing captures synchronized to the monitor's refresh rate.

## Features

- **SLLM (Self-Learning Logic Module)**:
  - Detects the most relevant user window based on:
    - Foreground (active) window
    - Keywords in the window title (e.g., "game", "code", "editor", etc.)
    - Adaptive usage-based scoring system
    - Optional support for Steam game titles
- **Refresh-aware capture**:
  - Automatically adjusts capture FPS to match the detected monitor refresh rate (e.g., 60Hz, 120Hz, 144Hz, etc.)
- **Region clipping**:
  - Ensures the capture area fits within screen boundaries
- **Self-learning**:
  - Stores and updates scores for frequently used windows to improve future detection
- **Auto-deletion**:
  - Automatically deletes screenshots after a set duration (default: 40 seconds)
- **Supports multi-monitor setups and various screen resolutions**
- 
<img width="617" height="1389" alt="fluxograma_dxcam_sllm" src="https://github.com/user-attachments/assets/ac185db5-d751-4f22-9719-12e8a92a1dd7" />

## Requirements

- **Operating System**: Windows 10 or later
- **Python**: 3.10 or higher (recommended to use a virtual environment)
- **Dependencies**:

```bash
pip install dxcam pygetwindow pywin32 pillow
Directory Structure.
window_scores.json: Adaptive score history by window title (auto-generated)

steam_titles.json: Optional list of Steam game titles (boosts game window detection)
How to Use:
Clone the repository: git clone https://github.com/your_user/dxcam-with-sllm.git
cd dxcam-with-sllm

Create and activate a virtual environment:
python -m venv .venv
.venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Run the script:
python dxcam_sllm.py


 
