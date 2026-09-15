# Battleship

## Introduction

Battleship is a graphical, turn-based naval strategy game built with Python and Pygame. Place your fleet on a 10-by-10 board, then take turns attacking the computer opponent's board. The game includes ship placement, rotation and clearing controls, hit and miss markers, an opponent AI, and win screens.

## Environment Requirements

- Python 3.10 to 3.13
- Pygame 2.5 or later
- A desktop environment that can open a Pygame window

All artwork and the game font are included in the `assets/` directory. Keep that directory next to `Battleship_Final_Project.py`.

## Installation

1. Clone or download this repository.
2. Open a terminal in the downloaded project folder.
3. Create and activate a virtual environment (recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell, activate it with:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

4. Install the dependency:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

## Usage

Run the game with:

```bash
python3 Battleship_Final_Project.py
```

The program locates its bundled assets automatically, so the command can be run from any working directory. The game opens in fullscreen mode. Use the menu to start a game or view the instructions. During ship placement, drag ships to the board, press `R` to rotate the selected ship, press `C` to clear the placement board, and select **Confirm** after placing every ship. Close the game window or choose **Quit** from the menu to exit.

## Collaboration Statement

This repository was completed in collaboration with fellow students at Penn State Altoona campus.
