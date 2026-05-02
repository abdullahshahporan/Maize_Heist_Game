<div align="center">

# 🌽 Maze Heist

### *Outsmart the AI. Collect the Loot. Escape the Maze.*

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame--CE-2.5.7-00B140?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

</div>

---

## 🎬 Gameplay Video

<div align="center">

<video src="https://github.com/abdullahshahporan/Maize_Heist_Game/raw/refs/heads/master/AI_Game.mp4" controls width="800">
  Your browser does not support the video tag.
</video>

*Watch Minimax AI vs A\* Tactical AI battle it out in real time!*

</div>

---

## 📖 About

**Maze Heist** is a turn-based, strategy maze game built with Python and Pygame. Two players navigate a procedurally generated maze, collecting treasures while tactically placing walls to block each other. Face off against a powerful **Minimax AI** with alpha-beta pruning, or watch two AIs battle it out!

> The player who collects the most treasure value wins. But watch out — the AI thinks several moves ahead!
---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Smart AI** | Minimax AI with alpha-beta pruning vs A* tactical pathfinding AI |
| 🗺️ **Procedural Mazes** | Every game generates a fresh, unique maze |
| 🧱 **Tactical Walls** | Place temporary walls to block opponents |
| 💎 **Treasure Hunting** | Collect cash, gold, and diamonds for points |
| 🎮 **Two Game Modes** | AI vs Human, or watch AI vs AI battles |
| 🔥 **Difficulty Levels** | Easy, Medium, and Hard |
| 📊 **Match Logging** | Game results are automatically saved to logs |
| 🏁 **Replay System** | Instantly replay a match with the same settings |

---

## 💰 Treasure Values

| Treasure | Points |
|:---:|:---:|
| 💵 Cash | 5 pts |
| 🥇 Gold | 10 pts |
| 💎 Diamond | 20 pts |

---

## 🎮 Game Modes

### 🤖 AI vs AI
Sit back and watch **Minimax AI** vs **A* Tactical AI** battle it out in real time. Great for studying strategies!

### 🧑‍💻 AI vs Human
You take on the role of **Player 2** and go head-to-head against the Minimax AI. How long can you last?

---

## 🕹️ Controls

### Movement
| Key | Action |
|:---:|:---|
| `↑` `↓` `←` `→` | Move your player |

### Wall Placement
| Key | Action |
|:---:|:---|
| `W` | Toggle **wall placement mode** |
| `↑` `↓` `←` `→` | (in wall mode) Aim at a wall edge |
| `Enter` | Confirm wall placement |

### General
| Key | Action |
|:---:|:---|
| `Esc` | Open exit / back to menu confirmation |
| `R` | Replay (on game-over screen) |
| `M` | Return to menu (on game-over screen) |
| `Q` | Quit game (on game-over screen) |
| `Y` / `N` | Confirm / cancel exit prompt |

---

## 🚀 Getting Started (Run from Source)

### Prerequisites
- Python 3.9 or later
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/abdullahshahporan/Maize_Heist_Game.git
cd Maize_Heist_Game

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the game
python main.py
```

---

## 🪟 Download & Play (Windows .exe)

> 🚧 **Coming soon!** A pre-built `MazeHeist.exe` will be released so anyone can play without installing Python.
<!-- PLACEHOLDER: Replace the link below once the .exe is uploaded to a GitHub Release -->
<!--
[![Download .exe](https://img.shields.io/badge/Download-MazeHeist.exe-blue?style=for-the-badge&logo=windows)](https://github.com/abdullahshahporan/Maize_Heist_Game/releases/latest)
-->

Once the release is available:
1. Go to the [**Releases**](https://github.com/abdullahshahporan/Maize_Heist_Game/releases) page
2. Download **`MazeHeist.exe`**
3. Double-click to play — **no installation required!**

### Build the .exe Yourself

If you'd rather build it locally:

```bash
# Install PyInstaller
pip install pyinstaller

# Run the build script
python build_exe.py
```

The executable will be created at `dist/MazeHeist.exe`. Share that single file with anyone — they don't need Python installed!

---

## 🗂️ Project Structure

```
Maize_Heist_Game/
│
├── main.py               # 🚀 Entry point — run this to start the game
├── config.py             # ⚙️  Global constants, colours, difficulty settings
├── build_exe.py          # 🔨 Script to build a standalone .exe
├── requirements.txt      # 📦 Python dependencies
│
├── game/                 # 🎯 Core game logic
│   ├── maze_generator.py #    Procedural maze generation
│   ├── game_state.py     #    Game state management
│   ├── board.py          #    Board representation
│   ├── entities.py       #    Player & treasure entities
│   ├── actions.py        #    Move and wall-placement actions
│   └── rules.py          #    Game rules and validation
│
├── ai/                   # 🤖 Artificial intelligence
│   ├── minimax_agent.py  #    Minimax with alpha-beta pruning
│   ├── alphabeta.py      #    Alpha-beta search core
│   ├── astar_agent.py    #    A* pathfinding agent
│   ├── heuristics.py     #    Evaluation heuristics
│   └── wall_logic.py     #    Wall-placement strategy
│
├── ui/                   # 🖼️  User interface & rendering
│   ├── renderer.py       #    Board and HUD drawing
│   ├── menu.py           #    Main menu
│   ├── screens.py        #    Opening / end screens
│   ├── input_handler.py  #    Human keyboard input
│   └── asset_manager.py  #    Sprite & asset loading
│
├── utils/                # 🛠️  Utilities
│   ├── pathfinding.py    #    BFS / pathfinding helpers
│   ├── helpers.py        #    Timer and misc helpers
│   └── logger.py         #    Match result logging
│
└── assets/               # 🎨 Sprites & graphics
    └── sprites/
```

---

## 🛠️ Tech Stack

- **Language:** Python 3.9+
- **Game Library:** [Pygame-CE](https://pyga.me/) 2.5.7
- **AI:** Minimax + Alpha-Beta Pruning, A* Search
- **Packaging:** PyInstaller (for .exe distribution)

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ and 🌽 by [abdullahshahporan](https://github.com/abdullahshahporan)

⭐ *If you enjoy the game, please give this repo a star!* ⭐

</div>
