# [Ray Engine Editor] - RayTk GameKit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) A simple, open-source game editor and engine built with Python, Tkinter, and Raylib. Create basic 3D grid-based FPS levels, customize assets and game settings through a user-friendly GUI, and instantly preview your creations.

## Table of Contents

-   [Features](#features)
-   [Getting Started](#getting-started)
    -   [Prerequisites](#prerequisites)
    -   [Installation](#installation)
-   [Usage](#usage)
    -   [Editor Interface](#editor-interface)
    -   [Map Editing](#map-editing)
    -   [Asset Management](#asset-management)
    -   [Game Settings](#game-settings)
    -   [Main Menu Configuration](#main-menu-configuration)
    -   [Saving & Loading](#saving--loading)
    -   [Previewing](#previewing)
-   [Dependencies](#dependencies)
-   [Contributing](#contributing)
-   [License](#license)
-   [Acknowledgements](#acknowledgements)

## Features

* **Graphical Map Editor:** Easy-to-use Tkinter-based GUI for level creation.
* **Grid-Based Design:** Build levels using walls, ground, player spawn points, and enemy placements on a 20x20 grid (configurable in code).
* **Real-time 3D Preview:** Instantly test and play your level using the integrated Raylib-based engine.
* **Asset Customization:**
    * Set custom textures for walls and ground.
    * Define handgun sprites for idle and shooting states.
    * Add custom shooting sounds (.wav, .ogg, .mp3 supported via Pygame Mixer).
    * Set custom enemy sprites for idle and 'hit' states.
    * Import custom `.obj` models for enemies (and potentially walls/ground if default `wall.obj` is replaced).
* **Environment Configuration:** Choose custom colors for the sky and sun.
* **Game Mechanics Configuration:**
    * Set game window title.
    * Adjust weapon shot delay.
    * Customize the win message text and color.
* **Customizable Main Menu:**
    * Set menu title and button text.
    * Align menu elements (left, middle, right).
    * Choose background (solid color or image).
    * Customize font colors for title and buttons.
* **Player Controls:** Standard FPS controls (WASD movement, mouse look, jumping, running).
* **Basic Enemy AI:** Enemies are static but react to being shot (displaying a 'hit' texture/state) and are removed after a set number of hits.
* **Simple Collision Detection:** Basic player-wall collision handling.
* **Portable Asset Management:** A `media` directory system automatically copies and manages assets, making projects easier to share.
* **Save/Load System:** Save and load entire map configurations (grid, assets, settings) and main menu layouts to/from `.json` files.

## Getting Started

### Prerequisites

* **Python 3.x:** Download from [python.org](https://www.python.org/)
* **pip:** Python package installer (usually included with Python).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
    cd your-repository-name
    ```
    2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    * *Note:* You need to create a `requirements.txt` file with the following content:
        ```txt
        raylibpy
        numpy
        pygame
        Pillow
        ```
    * Alternatively, install manually:
        ```bash
        pip install raylibpy numpy pygame Pillow
        ```

3.  **(Optional but Recommended) Default Assets:** Ensure you have default assets available, especially `wall.obj`, or the preview might have issues loading models. Consider including basic placeholder assets (textures, sounds, models) in the `media` directory or elsewhere in the repository for users to get started quickly.

## Usage

Run the editor using Python:

```bash
python your_main_script_name.py
