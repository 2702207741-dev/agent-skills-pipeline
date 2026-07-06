---
name: cg-extraction-workflow
description: Use when needing to extract, decrypt, or convert CG (computer graphics) assets from visual novels or Japanese games. Use when a game uses common engines like Kirikiri, ARTEMIS, Unity Live2D, or Ren'Py. Use when unpacking .xp3, .arc, or other game archives.
version: 1.0.0
metadata:
  tags: [game-assets, cg-extraction, visual-novel, reference]
  related_skills: [git-workflow-for-agents]
---

# CG Extraction Workflow

## Overview

Visual novel / eroge CG extraction is engine-specific: wrong tool = broken files. This skill covers 4 engines (Kirikiri, ARTEMIS, Ren'Py, Unity), a fallback brute-force approach, and safety practices to avoid corrupting original archives. Only use this skill on games you legally own.

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| Need to extract CG from a Kirikiri game (.xp3) | The game uses a custom/proprietary engine—research first |
| Need to unpack ARTEMIS engine .arc files | You just want to screenshot (use Snipping Tool / ShareX) |
| Need to extract Ren'Py game assets (archives only — rpa/rpi) | The game is already unpacked—walk the filesystem |
| Need to break Unity Live2D AssetBundle | You need to modify/recompile game code (not CG extraction) |
| The game has no known tools — try brute force | You are redistributing copyrighted assets |

## The Process

```
Identify engine (exe/scripts/.xp3/.arc/Unity) → Install tool → Extract → Convert (if needed) → Done
```

### Step 1: Identify Engine

**Expected Output:** Engine name (Kirikiri / ARTEMIS / Ren'Py / Unity / Unknown)

Look at the game's root directory and files:

- `*.xp3` files + `Kirikiri*.exe` or `krkr*.exe` → **Kirikiri** (TVP/Kirikiri 2/Z)
- `*.arc` files, often in a `data/` or `pack/` folder, exe not obviously other engine → **ARTEMIS**
- `*.rpa` / `*.rpi` files + `renpy/` directory → **Ren'Py**
- `*_Data/` folder with `*.unity3d` / AssetBundle files → **Unity**

```
Check game dir for:
  │
  ├── .xp3 present → Kirikiri
  ├── .arc present (no .xp3) → ARTEMIS
  ├── renpy/ dir or .rpa files → Ren'Py
  ├── *_Data/ + .unity3d → Unity
  └── none of above → Unknown (try Step 5 brute force)
```

**Common pitfalls:**
- Some games bundle multiple engines (e.g., Kirikiri for main, Unity for mini-games). Check subdirectories.
- Nekopara / similar may have .xp3 but use older Kirikiri variant—tool from Step 2 still works.

### Step 2: Install Extraction Tool

**Expected Output:** `tool --version` or confirmation the binary exists.

```
Engine:
  │
  ├── Kirikiri   → GARbro (GUI) or krkrz-xp3-tool (CLI)
  ├── ARTEMIS    → arc_unpacker (CLI, formerly arc_unpack.py or ArtemisUnpack)
  ├── Ren'Py     → unrpa (Python CLI)
  ├── Unity      → AssetStudio (GUI) or UnityEX (CLI)
  └── Unknown    → binwalk / `dd` hex search (Step 5)
```

**Commands:**

```bash
# Kirikiri - GARbro
# Download from https://github.com/morkt/GARbro (binary release), extract, run GARbro.GUI.exe

# Kirikiri - krkrz-xp3-tool CLI
git clone --depth 1 https://github.com/Project-Cube/krkrz-xp3-tool.git
cd krkrz-xp3-tool && make

# ARTEMIS - arc_unpacker
git clone --depth 1 https://github.com/Riku-m7/arc_unpacker.git
cd arc_unpacker && ./build.sh  # or download binary release

# Ren'Py - unrpa
pip install unrpa

# Unity - AssetStudio
# Download from https://github.com/Perfare/AssetStudio (binary release)
```

**If fails:** No binary release for your OS → check Wine compatibility (GARbro runs under Wine on Linux/macOS). arc_unpacker is Windows-native but has Linux build scripts.

### Step 3: Extract

**Expected Output:** Extracted files appear in output directory.

```bash
# Kirikiri - GARbro (GUI): Open .xp3 → Select all → Extract → choose output folder
# Kirikiri - CLI:
./krkrz-xp3-tool extract game.xp3 -o ./extracted/

# ARTEMIS - arc_unpacker CLI:
arc_unpacker --input game.arc --output ./extracted/

# Ren'Py - unrpa:
unrpa game.rpa -o ./extracted/

# Unity - AssetStudio (GUI): Open folder → Select AssetBundle → Export → Filter by texture type
```

```
After extraction, check output:
  │
  ├── .png / .jpg / .bmp → CG extracted successfully
  ├── .pvr / .ktx / .dds → needs conversion (Step 4)
  └── Empty or garbled → wrong tool or encrypted
```

**If fails:**
- Empty output → Try different tool variant (e.g., `xp3-tool-classic` for older Kirikiri)
- Corrupt files → The .xp3/.arc may be encrypted; search VNDB/game-specific forums for decryption key
- Permission denied → Run on a copy, not on the game install directory

### Step 4: Convert Formats (if needed)

**Expected Output:** `.png` or `.jpg` files for each CG.

Not all extracted files are viewable directly:

| Format | Tool | Command |
|--------|------|---------|
| .pvr (PowerVR) | PVRTexTool / TextureConverter | `PVRTexTool -f r8g8b8 -i input.pvr -o output.png` |
| .dds (DirectDraw) | ImageMagick / DirectXTex | `magick convert input.dds output.png` |
| .ktx (Khronos) | PVRTexTool / ktx2png | `ktx2png input.ktx output.png` |
| .bmp (raw) | ImageMagick | `magick convert input.bmp output.png` |
| .png (already CG) | Skip—already viewable | — |

```bash
# Batch convert (ImageMagick)
mkdir -p ./png && for f in *.dds; do magick convert "$f" "./png/${f%.*}.png"; done
```

**If fails:** Use GIMP with DDS/PVR plugin as fallback.

### Step 5: Brute Force (Unknown Engine)

**Expected Output:** Raw image bytes, or confirmation no embedded images found.

When no tool works:

1. **Run `file` on the archive** — it might be a known format but renamed:
   ```bash
   file unknown_game_file
   ```

2. **Check for magic bytes with binwalk:**
   ```bash
   pip install binwalk
   binwalk --signature unknown_archive
   ```

3. **Hex search for PNG/JPEG headers:**
   ```bash
   # Search for PNG magic bytes
   grep -oba $'\x89PNG' unknown_archive | head
   # Search for JPEG
   grep -oba $'\xff\xd8\xff' unknown_archive | head
   ```

4. **Extract raw image data with dd:**
   ```bash
   # After finding offset (e.g., 0x1234) and approximate size
   dd if=unknown_archive of=output.png bs=1 skip=$((0x1234)) count=$((0x100000))
   ```

**If this fails:** The archive is likely using proprietary encryption. Search the game title + "extract" + "tool" on VNDB or GitHub.

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| GARbro opens .xp3 but extract is empty | File uses encryption variant | Search VNDB or GitHub for game-specific decryption patch |
| arc_unpacker crashes on .arc | ARC version mismatch | Try specific commit of arc_unpacker: `git checkout v1.0.1` |
| Extract yields garbled/random colors | Wrong swizzle order or byte order | Use raw hex viewer—check if header looks like known format |
| Ren'Py .rpa won't open | rpa uses key indexing | `unrpa --file-list rpa` to get file list, then extract specific files |
| ImageMagick can't read .dds | DDS uses DX10 header (uncompressed) | Use DirectXTex or GIMP DDS plugin |
| Game uses custom engine | Developer created proprietary pack | Search GitHub for game title + "tool" or VNDB forum |

## Verification Checklist

- [ ] Step 1: Engine identified correctly (check dominant file extensions)
- [ ] Step 2: Tool installed and version confirmed
- [ ] Step 3: Files extracted to output directory
- [ ] Step 4: All CGs viewable as .png/.jpg
- [ ] Step 4: No broken/missing tiles in extracted images
- [ ] Step 5: Brute force attempted if applicable
