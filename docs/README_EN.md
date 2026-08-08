# Gravity Shift

> Note: This project is Ukrainian. All current project texts are maintained in Ukrainian as the primary language. The English version is secondary and intended as a draft/translation for reference.

`A cosmic platformer about finding yourself, gravity, space, and the non-obvious rules of the world.`

> Linear platformer Gravity Shift
>
> This is a game about journeys and puzzles in forgotten worlds.
>
> You are the player, shaped by unique abilities. You travel through worlds in the hope of finding clarity. Why are you here? What are you made of? Who created you? Where is the truth, anyway?

---

## ╰┈─┈─┈─┈─┈─┈─┈─╯

# 🪐 What is in the game

The game is rich in many features and functions that make up its universe.

Small details, such as acceleration and stopping, smooth camera movement, mathematical texturing of space, provide only the smallest drop of detail that can be present in this game.

## 👤 Player

An unknown substance. Depending on it, his features are determined.

It has gravitational properties, changing gravity upon touching its material of another polarity — this is what portals are.

It is able to shrink while falling, bypassing gravity.

It has a dash system (sprint) that helps overcome large distances or stop a fall if necessary.

## 🌌 Worlds

Unique spaces focused on capability and ease of development.

Each world has its own `main.py`, `objects.json`, `Resources` (music, pictures, sounds), and a personal grouping file (everything should reside in it).

All authorial details can be added to `main`.

## ✨ Visual Style

A classic Pygame style with additions of classic cosmic themes, with attention to options and support for custom creations (modding).

The game will have info panels divided into categories:

- User
- Developer
- Tips
- Settings
- Conversation (in the future)

Always unique textures are implemented using mathematics. Only the main attention objects are represented as images.

---

# ⚙️ Dependencies and package installation

## File structure

```plan
___________________________
├───────Gravy Shift───────┤
├── core_v#/               
│   ├── __init__.py        
│   ├── classes.py         
│   ├── lighting.py        
│   └── save.json          
│                          
├── 1_world/               
│   ├── Resources/         
│   │   ├── Music/...      
│   │   ├── Picture/...    
│   │   └── Sounds/...     
│   ├── main.py            
│   └── objects.json       
│                          
├── 2_world/  (якщо є)     
│   ├── Resources/         
│   │   ├── Music/...      
│   │   ├── Picture/...    
│   │   └── Sounds/...     
│   ├── main.py            
│   └── objects.json       
│                          
├── docs                   
│   ├── LICENSE            
│   ├── notes.txt          
│   ├── README_EN.md       
│   └── README.md          
│                          
├── README.md              
├── requirements.txt       
├── START_HERE.py          
└─────────────────────────┘
```

> Make sure the file structure is correct.

## Required packages

Before launching, it is necessary to install additional Python packages.

Required libraries:

- `python`
- `pygame`
- `colorama`
- `moderngl`
- `numpy`

For convenience, it is recommended to use `pip` and the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## System requirements

- Windows 10/11 or a compatible OS.
- Python (ver 3.8+, ver printed game 3.13.7 also 3.13.14).
- Updated graphics drivers with OpenGL support (for `moderngl`).
- Audio may work through standard Windows sound drivers.

You can start the game using `START_HERE.py` (main menu and navigation)
or by manually invoking the required `main.py` file.

---

# 🧩 How the code works and flexibility

## Architecture

The game rules and texture are located in the `core_v#/classes.py` folder (main classes for the player, objects, scenes), `lighting.py` (lighting), and `save.json` (saving).

The logic of a specific world is located in each respective world module, for example `MARS_world/`, and has its own `main.py` and `objects.json`.

## Interaction model

Through `START_HERE.py`, you can load the world `main.py` and start the game.

In the `main.py` code, a list of objects is connected from `objects.json` and the necessary modules from `classes.py` are activated — they provide ready-made logic for existing objects, cameras, and textures.

## Flexibility

The system is designed modularly: add a new world — create a folder with `main.py`, `objects.json`, and `Resources/` (music, pictures, sounds). The engine will automatically pick up standard files by convention. It will also draw a new planet on the main menu, ready to launch.

## Comfort

The code is filled with notes and history about its structure. In places of interlude, there will be explanations of what lines do. Headers have been created for most of the main classes and functions.

---

# 🧭 For those who want to make their own mod

Create a folder named `NAME_world/` (make sure to keep `_world` in the name for self-recognition) next to the other worlds and add:

- `main.py` — entry point and level logic (add all your new features and rules here and activate the game loop);
- `objects.json` — description of all objects (positions, types, properties);
- `Resources/` → `Music/`, `Picture/`, `Sounds/` — media files for the level.

## Interface with `core_v#`

In `main.py`, connect the required classes directly, for example:

```python
from core_v1.classes import Player, Platform, TunnelPortal, JumpPad, Campfire, Finish
```

## Rules and events

Define your own rules in `main.py` (for example, an unconventional gravity, movement modes) and handle them in your code instead of changing the core.

## Saving

To save the state, use `save_full_progress()` and `standart_progress()` or make your own calls to `save.json` according to the format convention.

## Features for developers

- `DEV_MODE`: the core has a developer mode built in to improve the experience, analytics, and other useful features.
  - While developing, enable `DEV_MODE` to:
    - see entity positions in real time;
    - check different variables (by switching them off or on);
    - use the mouse to mark and extract objects;
    - have privileges in the game (between control and view).
- JSON level loading system: loading through `objects.json` provides a convenient, declarative model of levels — easy to version and edit with external tools. Autonumbering by index will help keep track of the number of objects.
- ModernGL and GLSL (SDF-based): if ModernGL and custom GLSL shaders are integrated into the core, use them to offload rendering and visual effects — this improves performance and grants access to modern graphics techniques. (Separating responsibilities between CPU and GPU)

---

# ⚡ For optimization-sensitive users

My computer is not one of the most powerful either, so my code has been focused on quality from the very beginning. Here is what has already been done and what can still be emphasized:

- The size of the game window directly affects the amount of visible space and the amount of CPU calculations;
- In the `lighting.py` file, the line `self.downscale` affects the proportional number of pixels calculated (`4` times for `1600x900` = `400x225`, which is `1 440 000` versus `90 000` pixels!);
- Info panels are drawn only when they appear and when there is new information (no 60 times per second, only overlays);
- `DEV_MODE` adds auxiliary elements and diagnostics, but it also increases costs — for regular play, keep it disabled.

## Tips for users who want to make the game easier without changing the mechanics

- Reduce the window resolution or run the game in a smaller window;
- Disable the info panels (`F9`), if you need a dry game without details;
- Keep the developer mode and other debugging settings turned off (these panels update periodically);
- Use simpler modes with fewer active objects and logic;
- And for the more advanced modders, try to avoid an excessive number of objects in the world. Where possible, use one or fewer.

> (Undeveloped point)
>
> To create objects that are on the surface and under the shadow, use `"indoor": true` in the `platforms` dictionary to artificially remove sunlight.

> (More points will be added here)

---

# 📝 Authorship and user rights (Short version)

## Authorship and protection

This project, its core (`core_v#/`) and all basic architecture are designed and protected by copyright:

- Game author: Moorzik Kin / Bohdan Nikolayets

## Rules for code use

Executing the code by the player is usage permitted within a single game installation.

### User:

- ✓ May run the game and play it;
- ✓ May explore the code for learning;
- ✗ May not directly copy fragments of code and present the project as their own;
- ✗ May not distribute a modified core as a separate product.

## Authorship of mods and extensions

The user will have authorship over the modifications they create themselves. They may change and expand only:

- `main.py` (logic and rules of their world);
- `objects.json` (object configuration);
- `Resources/` (music, pictures, sounds of their world);
- Their personal group file (the folder containing the above items).

## Distribution of mods

Mods may be distributed separately as additions to Gravity Shift, provided that:

- the authorship of the modification is indicated;
- the original Gravity Shift game is preserved as a separate product;
- there is no distribution of the core `core_v#/` or base code as part of the mod.

> Mods themselves may not run without the original game. This is normal for add-ons — they should work together with Gravity Shift, but not be a full standalone game.

> More details about authorship, core restrictions, user rights, and modding rules are described in a separate legal-document [LICENSE](LICENSE). There it is established that the original engine and basic game logic remain under copyright control, while personal `_world` content may develop as original mod content.

---

# M.
