"""
build_exe.py — Build a standalone .exe for Maze Heist.

Run:  python build_exe.py
Output:  dist/MazeHeist.exe  (single-file distribution)

Just send MazeHeist.exe to anyone — they double-click to play.
"""

import PyInstaller.__main__
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")

# Check for an .ico; if there isn't one, omit --icon
icon_path = os.path.join(ASSETS, "icon.ico")
icon_arg = f"--icon={icon_path}" if os.path.exists(icon_path) else None

args = [
    os.path.join(ROOT, "main.py"),
    "--name=MazeHeist",
    "--onefile",                           # single .exe
    "--windowed",                          # no console window
    f"--add-data={ASSETS};assets",         # bundle the assets folder
    "--noconfirm",                         # overwrite without asking
    "--clean",
    f"--distpath={os.path.join(ROOT, 'dist')}",
    f"--workpath={os.path.join(ROOT, 'build')}",
    f"--specpath={ROOT}",
]

if icon_arg:
    args.append(icon_arg)

# Hidden imports that PyInstaller may not detect automatically
args += [
    "--hidden-import=pygame",
    "--hidden-import=game",
    "--hidden-import=game.board",
    "--hidden-import=game.entities",
    "--hidden-import=game.actions",
    "--hidden-import=game.rules",
    "--hidden-import=game.game_state",
    "--hidden-import=game.maze_generator",
    "--hidden-import=ai",
    "--hidden-import=ai.alphabeta",
    "--hidden-import=ai.minimax_agent",
    "--hidden-import=ai.astar_agent",
    "--hidden-import=ai.heuristics",
    "--hidden-import=ai.tactical_blocker",
    "--hidden-import=ui",
    "--hidden-import=ui.asset_manager",
    "--hidden-import=ui.renderer",
    "--hidden-import=ui.menu",
    "--hidden-import=ui.screens",
    "--hidden-import=ui.input_handler",
    "--hidden-import=utils",
    "--hidden-import=utils.pathfinding",
    "--hidden-import=utils.helpers",
    "--hidden-import=utils.logger",
    "--hidden-import=config",
]

print("Building MazeHeist.exe (single-file) ...")
PyInstaller.__main__.run(args)
print("\nDone!  Your .exe is at:  dist/MazeHeist.exe")
print("Send that single file to anyone — no installation needed.")
