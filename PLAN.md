# Visual Novel Prototype Plan

## Project Overview
Create a modern visual novel prototype with full UX functionality, ready for asset integration. Initially in Chinese with English localization planned.

---

## 1. Tech Stack Recommendation

### Primary Choice: **Ren'Py**

| Criteria | Ren'Py | Unity+Naninovel | Godot+Dialogic | Custom Web |
|----------|--------|-----------------|----------------|------------|
| VN-specific features | Built-in | Plugin ($150+) | Plugin | From scratch |
| Save/Load/Skip | Built-in | Built-in | Partial | From scratch |
| Localization | Excellent | Good | Basic | Manual |
| 1440p Support | Yes | Yes | Yes | Yes |
| Learning Curve | Low | Medium | Medium | High |
| Build Size | Small (~50MB) | Large (~200MB+) | Medium | Small |
| Community/Docs | Excellent for VN | General | Growing | N/A |
| Cost | Free | Unity+$150 | Free | Free |

**Recommendation: Ren'Py** because:
1. Purpose-built for visual novels - all core features are built-in
2. Excellent Chinese/CJK text support out of the box
3. Built-in translation system for English version later
4. Handles resolution scaling elegantly
5. Python-based scripting (easy to read/write)
6. Industry standard (Doki Doki Literature Club, countless commercial VNs)
7. Cross-platform: Windows, Mac, Linux, Android, iOS, Web export

**When to consider alternatives:**
- Unity: If you need complex gameplay mechanics (RPG systems, mini-games)
- Godot: If this will become a hybrid VN/game with heavy gameplay
- Web: If browser-first deployment is critical

---

## 2. Resolution & Display Strategy

### Base Resolution: 1920x1080 (Full HD)
- Scales cleanly to 1440p (2560x1440)
- Scales down to 720p for lower-end devices
- Ren'Py handles letterboxing/pillarboxing automatically

### Asset Specifications (for artists)
| Asset Type | Recommended Size | Format |
|------------|------------------|--------|
| Backgrounds | 1920x1080 (or 2560x1440 for 1440p native) | PNG/WebP |
| Character Sprites | ~1200-1600px height | PNG (transparent) |
| CG/Event Images | 1920x1080 | PNG/JPG |
| UI Elements | Vector or 2x scale | PNG (transparent) |

---

## 3. Project Structure

```
Endless Summer Syndrome Demo/
├── game/
│   ├── audio/
│   │   ├── bgm/              # Background music
│   │   ├── sfx/              # Sound effects
│   │   └── ambient/          # Ambient sounds
│   │
│   ├── images/
│   │   ├── bg/               # Backgrounds
│   │   ├── cg/               # CG/Event images
│   │   ├── sprites/          # Character sprites
│   │   │   └── [character]/
│   │   └── ui/               # UI elements
│   │
│   ├── gui/                  # Ren'Py GUI assets
│   │
│   ├── scripts/
│   │   ├── story/            # Story scripts by chapter/scene
│   │   │   ├── chapter1.rpy
│   │   │   ├── chapter2.rpy
│   │   │   └── ...
│   │   ├── characters.rpy    # Character definitions
│   │   └── variables.rpy     # Game variables/flags
│   │
│   ├── tl/                   # Translations
│   │   └── english/          # English translation (later)
│   │
│   ├── screens.rpy           # Custom UI screens
│   ├── options.rpy           # Game configuration
│   ├── gui.rpy               # GUI styling
│   └── script.rpy            # Entry point
│
├── PLAN.md                   # This file
├── ASSET_SPECS.md            # Specifications for artists
└── README.md                 # Project documentation
```

---

## 4. Feature Checklist

### Core UX (Built-in, needs configuration)
- [x] Left-click to advance dialogue
- [x] Right-click to open game menu
- [x] Skip (hold Ctrl)
- [x] Auto-read mode
- [x] Save system (multiple slots)
- [x] Load system
- [x] Backlog/History (scroll wheel up)
- [x] Quick Save/Quick Load
- [x] Preferences (text speed, volume, fullscreen, etc.)

### UI Screens to Customize
- [ ] Main Menu (标题画面)
- [ ] In-game Textbox (对话框)
- [ ] Character Namebox (名字框)
- [ ] Game Menu (游戏菜单)
- [ ] Save/Load Screen (存档界面)
- [ ] Preferences Screen (设置界面)
- [ ] History Screen (历史记录)
- [ ] Confirm Dialogs (确认对话框)

### Additional Features
- [ ] Music room (音乐鉴赏)
- [ ] Ending flags tracking (2 endings)
- [ ] Choice system with branching paths

---

## 5. Localization Strategy

### Phase 1: Chinese (Simplified) as Default
```python
# In options.rpy
define config.language = None  # Default is Chinese
```

### Phase 2: English Translation
Ren'Py's built-in translation system:
1. Write all dialogue in Chinese first
2. Run `renpy.sh <project> translate english` to extract strings
3. Translate strings in `game/tl/english/`
4. Players can switch language in preferences

### Text Considerations
- Use appropriate Chinese fonts (思源黑体/Source Han Sans recommended)
- Set proper text speed for Chinese reading pace
- Plan for text expansion in English (~30% longer than Chinese)

---

## 6. Development Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Install Ren'Py SDK
- [ ] Initialize project with proper structure
- [ ] Configure resolution (1920x1080 base)
- [ ] Set up Chinese font and text settings
- [ ] Create placeholder assets (colored rectangles)
- [ ] Test basic dialogue flow

### Phase 2: Core Systems (Week 2)
- [ ] Define all characters with placeholder sprites
- [ ] Implement scene structure from script
- [ ] Set up all game variables/flags
- [ ] Configure save/load system
- [ ] Test skip and auto-read

### Phase 3: UI Prototype (Week 2-3)
- [ ] Design and implement main menu (placeholder)
- [ ] Customize textbox appearance
- [ ] Customize game menu
- [ ] Customize save/load screens
- [ ] Customize preferences screen
- [ ] Add all necessary buttons (skip, auto, menu, etc.)

### Phase 4: Polish & Documentation (Week 3-4)
- [ ] Test all UX flows thoroughly
- [ ] Create ASSET_SPECS.md for artists
- [ ] Document how to replace placeholders
- [ ] Prepare translation structure for English
- [ ] Create build test for Windows

### Phase 5: Asset Integration (When ready)
- [ ] Replace placeholder backgrounds
- [ ] Replace placeholder sprites
- [ ] Replace placeholder UI
- [ ] Add music and sound effects
- [ ] Final testing and polish

---

## 7. Prototype Deliverables

At the end of prototyping, we will have:

1. **Fully functional game skeleton**
   - All UX interactions working
   - Placeholder visuals in correct positions
   - All menus and screens functional

2. **Asset pipeline ready**
   - Clear naming conventions
   - Documented size/format requirements
   - Drop-in replacement system

3. **Script integration ready**
   - Character definitions complete
   - Scene structure in place
   - Variable system for story flags

4. **Localization ready**
   - Chinese as default language
   - Translation file structure prepared
   - Font system configured

---

## 8. Technical Decisions (Confirmed)

| Decision | Answer |
|----------|--------|
| Base resolution | 1920x1080 (scales to 1440p) |
| Aspect ratio | 16:9 standard |
| Voice acting | No (not planned) |
| Choices/Branching | Yes - player choices, 2 endings |
| Special features | Music room only |
| Target platforms | PC primary (Steam), Mobile as stretch goal |

---

## 9. Platform & Distribution

### Steam (Primary)
Ren'Py has excellent Steam support:
- Native Steamworks integration (achievements, cloud saves)
- Easy to generate Steam-ready builds
- Many successful Ren'Py VNs on Steam

**Steam requirements we'll prepare:**
- [ ] Steam-compatible build configuration
- [ ] Achievement hooks (optional, can add later)
- [ ] Cloud save support (built into Ren'Py)
- [ ] Trading cards assets (art team responsibility)

### Mobile (Stretch Goal)
Ren'Py supports Android and iOS natively:
- **Complexity**: Low for basic support, medium for polish
- **Main consideration**: Touch-friendly UI (larger buttons, swipe gestures)
- **Approach**: Build for PC first, then test mobile build. If UI works reasonably, minimal changes needed. If not, we can add a mobile UI variant.

Ren'Py mobile features:
- Tap to advance (maps to left-click)
- Two-finger tap for menu (maps to right-click)
- Swipe for history
- Built-in touch keyboard if needed

---

## 10. Next Steps

1. ~~Review and discuss this plan~~ Done
2. ~~Confirm technical decisions~~ Done
3. Install Ren'Py SDK (version 8.x recommended)
4. Begin Phase 1 implementation

---

*Plan created: 2024-12-13*
*Status: Draft - Awaiting Review*
