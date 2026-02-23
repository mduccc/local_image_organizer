# Local Image Category Organizer (Python + CLIP)

Turn a huge, messy photo folder into a **clean, category-based library**.  
This tool runs **fully locally**, uses **CLIP** to understand image content, and then **sorts images into semantic categories** you define (family, documents, screenshots, memes, landscapes, etc.) by moving or copying them into per‑category folders.

- Focused on **category-based organization**: every image is assigned to the **single best category**.
- Supports: **Windows** (including AMD, CPU-only) and **macOS**.
- No cloud API calls; everything uses local models.
- Categories are fully configurable in `config.yaml`.

---

## 1. Environment requirements

- Python **3.9+** (recommended: 3.10/3.11)
- Internet only needed once to download the CLIP model (via `open_clip_torch`); after that everything runs locally on CPU.

---

## 2. Installation

In the project directory (where `requirements.txt` is located):

```bash
cd /path/to/local_image_org

# (Recommended) create a virtualenv
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Project structure

```text
local_image_org/
  README.md
  requirements.txt
  config.yaml
  image_sorter/
    __init__.py
    cli.py
    config.py
    model.py
    categorize.py
    fs_ops.py
```

---

## 4. Category configuration (`config.yaml`)

The heart of the organizer is `config.yaml`. It defines:

- **model**: which CLIP model and device to use.
- **categories**: the semantic categories you want to organize into.
- **thresholds**: minimum similarity before assigning a category.
- **behavior**: move vs copy, whether to keep original folder structure, and dry‑run mode.
- **files**: which file extensions (image formats) to scan.

Each category has:

- an `id` (used as the folder name),
- a human‑friendly `name`,
- several English `prompts` that describe that category’s typical images.

Minimal example:

```yaml
model:
  name: "ViT-B-32"
  pretrained: "laion2b_s34b_b79k"
  device: "cpu"

categories:
  - id: "people_family"
    name: "People / family photos"
    prompts:
      - "a photo of family at home"
      - "portrait of a person"
  - id: "landscape"
    name: "Landscape photos"
    prompts:
      - "landscape photo with nature"

thresholds:
  similarity_min: 0.22

behavior:
  move_files: true          # true = move, false = copy
  keep_folder_structure: false
  dry_run: true             # true = test only, no file operations

files:
  extensions:
    - ".jpg"
    - ".jpeg"
    - ".png"
```

**Category design tips**:

- Think like a photographer or curator: define categories that reflect how you actually search for photos (family, travel, food, invoices, memes, screenshots, UI mocks, etc.).
- Use multiple, clear English prompts per category to give CLIP a strong sense of each class.
- Adjust `similarity_min`:
  - Lower → more aggressive assignment (fewer `uncategorized`, more risk of mislabels).
  - Higher → safer but more images go to `uncategorized`.

---

## 5. CLI usage

The CLI entry point is `image_sorter/cli.py`. Run it as a module:

```bash
python -m image_sorter.cli --src "<source_folder>" --dst "<target_folder>" [options]
```

### Main arguments

- **Required**
  - `--src` : folder containing your unsorted images.
  - `--dst` : destination root folder; subfolders per category will be created here.
- **Optional**
  - `--config` : path to YAML config file (default `config.yaml`).
  - `--dry-run` : print the category plan only, **do not** move/copy files (overrides `behavior.dry_run`).
  - `--no-dry-run` : disable dry‑run and actually perform file operations.
  - `--move` : move files instead of copying (overrides `behavior.move_files`).
  - `--copy` : copy files instead of moving.
  - `--keep-structure` : inside each category folder, preserve the original subfolder structure from `--src`.
  - `--flat` : do not preserve structure; every image in a category goes into the same category folder.
  - `--max-images N` : process at most N images (great for testing category design).

---

## 6. Usage examples

### 6.1. Safe test run (dry‑run, category plan only)

Windows (PowerShell):

```powershell
python -m image_sorter.cli `
  --src "D:\Photos\Unsorted" `
  --dst "D:\Photos\Sorted" `
  --config "config.yaml" `
  --dry-run `
  --max-images 100
```

macOS (bash/zsh):

```bash
python -m image_sorter.cli \
  --src "/Users/me/Pictures/Unsorted" \
  --dst "/Users/me/Pictures/Sorted" \
  --config "config.yaml" \
  --dry-run \
  --max-images 100
```

The CLI will print lines like:

```text
[DRY-RUN] MOVE D:\Photos\Unsorted\img001.jpg -> D:\Photos\Sorted\people_family\img001.jpg
```

You can inspect the per‑category destination paths before trusting the automatic organizer.

### 6.2. Real category‑based re‑organization

After validating with a dry‑run:

```powershell
python -m image_sorter.cli `
  --src "D:\Photos\Unsorted" `
  --dst "D:\Photos\Sorted" `
  --config "config.yaml" `
  --no-dry-run `
  --move
```

This will **move** each image from `Unsorted` into a folder under `Sorted/<category_id>/...` based on its most likely category.

To **copy** instead of move:

```powershell
python -m image_sorter.cli `
  --src "D:\Photos\Unsorted" `
  --dst "D:\Photos\Sorted" `
  --config "config.yaml" `
  --no-dry-run `
  --copy
```

---

## 7. How the category organizer works

High‑level flow:

1. Load `config.yaml` and the CLIP model (`open_clip_torch`) in **CPU** mode by default.
2. For each category:
   - Encode all English `prompts` into text embeddings.
   - Average and normalize them into a single **category embedding**.
3. Walk through all images in `--src`, filtering by the configured extensions (`.jpg`, `.jpeg`, `.png`, `.gif`, `.heic`, etc.).
4. For each image:
   - Load with Pillow and apply CLIP preprocessing.
   - Encode into an **image embedding**.
   - Compute cosine similarity against every category embedding.
   - Pick the category with the highest similarity:
     - If it is above `similarity_min` → assign that category.
     - Otherwise → fall back to `uncategorized`.
   - Build the destination path (`--dst` + category id + optional preserved subpath).
   - Move/copy the file there (or just print the action in `dry-run` mode).

At the end you get a **folder tree organized by semantic categories**, not by date or original app.

---

## 8. Tuning your category system

- Start with a **small, high‑level set of categories** (e.g. `people_family`, `travel`, `documents`, `screenshots`, `memes`, `food`, `pets`).
- Run a dry‑run with `--max-images` on a sample to see where things land.
- Then:
  - Split overloaded categories (e.g. `travel` → `beach`, `mountains`, `cityscape`).
  - Merge categories that are too similar if you don’t care about that distinction.
  - Improve prompts to emphasize what you *do* and *don’t* want in each category.

This iteration is where the organizer really becomes tailored to how **you** think about your images.

---

## 9. GPU (optional)

If your machine has a GPU and you want faster categorization:

```yaml
model:
  name: "ViT-B-32"
  pretrained: "laion2b_s34b_b79k"
  device: "cuda"
```

If you don’t have a GPU, leave `device: "cpu"`; the code is written to work fine on CPU‑only machines (including AMD CPUs on Windows).

---

## 10. Current limitations & next ideas

- No detailed CSV/JSON logging yet (file → category, similarity score).  
  That would be useful for auditing and manual relabeling.
- No GUI; this is a CLI‑only tool for now.

Possible next steps:

- Add CSV logging of `(file_path, category_id, similarity)`.
- Provide a small review script to quickly reassign or revert categories.
- Expose a “top‑N categories per image” mode for deeper analysis.

# Local Image Organizer (Python + CLIP)

This tool helps you clean up a messy photo folder on your computer. It runs **fully locally**, uses **CLIP** to classify images into categories you define, then **moves/copies** those images into corresponding folders.

- Supports: **Windows** (including AMD, CPU-only) and **macOS**
- No cloud API calls; everything uses local models
- Flexible categories: edit them in `config.yaml`

---

## 1. Environment requirements

- Python **3.9+** (recommended: 3.10/3.11)
- Internet only needed to download the CLIP model once (via `open_clip_torch`); after that everything runs locally

---

## 2. Installation

In the project directory (where `requirements.txt` is located):

```bash
cd /path/to/local_image_org

# (Recommended) create a virtualenv
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Project structure

```text
local_image_org/
  README.md
  requirements.txt
  config.yaml
  image_sorter/
    __init__.py
    cli.py
    config.py
    model.py
    categorize.py
    fs_ops.py
```

---

## 4. Configuration (`config.yaml`)

The `config.yaml` file controls:

- **model**: CLIP variant, checkpoint, device (default `cpu`)
- **categories**: categories to classify into (id, display name, English prompts describing the category)
- **thresholds**: minimum similarity threshold
- **behavior**: move/copy mode, whether to keep original folder structure, dry-run mode
- **files**: image file extensions to scan

Minimal example:

```yaml
model:
  name: "ViT-B-32"
  pretrained: "laion2b_s34b_b79k"
  device: "cpu"

categories:
  - id: "people_family"
    name: "People / family photos"
    prompts:
      - "a photo of family at home"
      - "portrait of a person"
  - id: "landscape"
    name: "Landscape photos"
    prompts:
      - "landscape photo with nature"

thresholds:
  similarity_min: 0.22

behavior:
  move_files: true          # true = move, false = copy
  keep_folder_structure: false
  dry_run: true             # true = test only, no file operations

files:
  extensions:
    - ".jpg"
    - ".jpeg"
    - ".png"
```

**Tips**:

- The more clearly you describe each category in English prompts, the better CLIP will perform.
- You can add categories like `document`, `screenshot`, `food`, `meme`, etc.
- Tune `similarity_min`: if it is too low, misclassification increases; if too high, many images will end up as `uncategorized`.

---

## 5. CLI usage

The CLI entry point is in `image_sorter/cli.py`, run it as a module:

```bash
python -m image_sorter.cli --src "<source_folder>" --dst "<target_folder>" [options]
```

### Main arguments

- **Required**
  - `--src` : folder containing the unsorted images (input).
  - `--dst` : destination folder (where sorted images will be moved/copied).
- **Optional**
  - `--config` : path to YAML config file (default `config.yaml`).
  - `--dry-run` : print plan only, **do not** move/copy files (overrides `behavior.dry_run`).
  - `--no-dry-run` : disable dry-run (actually performs file operations).
  - `--move` : move files instead of copying (overrides `behavior.move_files`).
  - `--copy` : copy files instead of moving.
  - `--keep-structure` : preserve original subfolder structure under each category.
  - `--flat` : do not preserve structure; all images of a category go into a single folder.
  - `--max-images N` : process at most N images (useful for testing).

---

## 6. Usage examples

### 6.1. Safe test run (dry-run)

Windows (PowerShell):

```powershell
python -m image_sorter.cli `
  --src "D:\Photos\Unsorted" `
  --dst "D:\Photos\Sorted" `
  --config "config.yaml" `
  --dry-run `
  --max-images 100
```

macOS (bash/zsh):

```bash
python -m image_sorter.cli \
  --src "/Users/me/Pictures/Unsorted" \
  --dst "/Users/me/Pictures/Sorted" \
  --config "config.yaml" \
  --dry-run \
  --max-images 100
```

The CLI will print lines like:

```text
[DRY-RUN] MOVE D:\Photos\Unsorted\img001.jpg -> D:\Photos\Sorted\people_family\img001.jpg
```

### 6.2. Real run (move files)

After validating with a dry-run:

```powershell
python -m image_sorter.cli `
  --src "D:\Photos\Unsorted" `
  --dst "D:\Photos\Sorted" `
  --config "config.yaml" `
  --no-dry-run `
  --move
```

Or if you prefer to **copy** instead of move:

```powershell
python -m image_sorter.cli `
  --src "D:\Photos\Unsorted" `
  --dst "D:\Photos\Sorted" `
  --config "config.yaml" `
  --no-dry-run `
  --copy
```

---

## 7. How it works

High-level pipeline:

1. Load `config.yaml` and the CLIP model (`open_clip_torch`) in **CPU** mode (by default).
2. For each category:
   - Encode all its `prompts` into embeddings.
   - Average and normalize them into a single vector.
3. Iterate over all images in `--src` (filtered by extension).
4. For each image:
   - Load with Pillow and apply the CLIP preprocessing.
   - Encode into an image embedding.
   - Compute cosine similarity against every category embedding.
   - Pick the category with the highest similarity; if it is below `similarity_min`, the image becomes `uncategorized`.
   - Build the destination path (`--dst` + category id + optional preserved subpath).
   - Move/copy files or just print actions if in `dry-run` mode.

---

## 8. Tips & extensions

- **Speed optimization**:
  - Use `--max-images` to quickly test config/category behavior before running on the full dataset.
  - Later you can implement image batching to better leverage PyTorch’s vectorization.
- **Tuning categories**:
  - If many images are misclassified:
    - Refine or add prompts with clearer descriptions.
    - Adjust `similarity_min`.
    - Split broad categories into 2–3 more specific ones.
- **GPU (optional)**:
  - If your machine has a GPU, you can set in `config.yaml`:
    ```yaml
    model:
      name: "ViT-B-32"
      pretrained: "laion2b_s34b_b79k"
      device: "cuda"
    ```
  - If not, leave it as `cpu` (default).

---

## 9. Current limitations

- No detailed CSV/JSON logging yet (file → category, score). This can be added later.
- No GUI; only a CLI interface for now.

If you want CSV logging of classification results or a helper script to **revert** / change categories after running, those can be added as next steps.

# Local Image Organizer (Python + CLIP)

This tool helps you clean up a messy photo folder on your computer. It runs **fully locally**, uses **CLIP** to classify images into categories you define, then **moves/copies** those images into corresponding folders.

- Supports: **Windows** (including AMD, CPU-only) and **macOS**
- No cloud API calls; everything uses local models
- Flexible categories: edit them in `config.yaml`

---

## 1. Environment requirements

- Python **3.9+** (recommended: 3.10/3.11)
- Internet only needed to download the CLIP model once (via `open_clip_torch`); after that everything runs locally

---

## 2. Installation

In the project directory (where `requirements.txt` is located):

```bash
cd /path/to/local_image_org

# (Recommended) create a virtualenv
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Project structure

```text
local_image_org/
  README.md
  requirements.txt
  config.yaml
  image_sorter/
    __init__.py
    cli.py
    config.py
    model.py
    categorize.py
    fs_ops.py
```

---

## 4. Configuration (`config.yaml`)

The `config.yaml` file controls:

- **model**: CLIP variant, checkpoint, device (default `cpu`)
- **categories**: categories to classify into (id, display name, English prompts describing the category)
- **thresholds**: minimum similarity threshold
- **behavior**: move/copy mode, whether to keep original folder structure, dry-run mode
- **files**: image file extensions to scan

Minimal example:

```yaml
model:
  name: "ViT-B-32"
  pretrained: "laion2b_s34b_b79k"
  device: "cpu"

categories:
  - id: "people_family"
    name: "People / family photos"
    prompts:
      - "a photo of family at home"
      - "portrait of a person"
  - id: "landscape"
    name: "Landscape photos"
    prompts:
      - "landscape photo with nature"

thresholds:
  similarity_min: 0.22

behavior:
  move_files: true          # true = move, false = copy
  keep_folder_structure: false
  dry_run: true             # true = test only, no file operations

files:
  extensions:
    - ".jpg"
    - ".jpeg"
    - ".png"
```

**Tips**:

- The more clearly you describe each category in English prompts, the better CLIP will perform.
- You can add categories like `document`, `screenshot`, `food`, `meme`, etc.
- Tune `similarity_min`: if it is too low, misclassification increases; if too high, many images will end up as `uncategorized`.

---

## 5. CLI usage

The CLI entry point is in `image_sorter/cli.py`, run it as a module:

```bash
python -m image_sorter.cli --src "<source_folder>" --dst "<target_folder>" [options]
```

### Main arguments

- **Required**
  - `--src` : folder containing the unsorted images (input).
  - `--dst` : destination folder (where sorted images will be moved/copied).
- **Optional**
  - `--config` : path to YAML config file (default `config.yaml`).
  - `--dry-run` : print plan only, **do not** move/copy files (overrides `behavior.dry_run`).
  - `--no-dry-run` : disable dry-run (actually performs file operations).
  - `--move` : move files instead of copying (overrides `behavior.move_files`).
  - `--copy` : copy files instead of moving.
  - `--keep-structure` : preserve original subfolder structure under each category.
  - `--flat` : do not preserve structure; all images of a category go into a single folder.
  - `--max-images N` : process at most N images (useful for testing).

---

## 6. Usage examples

### 6.1. Safe test run (dry-run)

Windows (PowerShell):

```powershell
python -m image_sorter.cli `
  --src "D:\Photos\Unsorted" `
  --dst "D:\Photos\Sorted" `
  --config "config.yaml" `
  --dry-run `
  --max-images 100
```

macOS (bash/zsh):

```bash
python -m image_sorter.cli \
  --src "/Users/me/Pictures/Unsorted" \
  --dst "/Users/me/Pictures/Sorted" \
  --config "config.yaml" \
  --dry-run \
  --max-images 100
```

The CLI will print lines like:

```text
[DRY-RUN] MOVE D:\Photos\Unsorted\img001.jpg -> D:\Photos\Sorted\people_family\img001.jpg
```

### 6.2. Real run (move files)

After validating with a dry-run:

```powershell
python -m image_sorter.cli `
  --src "D:\Photos\Unsorted" `
  --dst "D:\Photos\Sorted" `
  --config "config.yaml" `
  --no-dry-run `
  --move
```

Or if you prefer to **copy** instead of move:

```powershell
python -m image_sorter.cli `
  --src "D:\Photos\Unsorted" `
  --dst "D:\Photos\Sorted" `
  --config "config.yaml" `
  --no-dry-run `
  --copy
```

---

## 7. How it works

High-level pipeline:

1. Load `config.yaml` and the CLIP model (`open_clip_torch`) in **CPU** mode (by default).
2. For each category:
   - Encode all its `prompts` into embeddings.
   - Average and normalize them into a single vector.
3. Iterate over all images in `--src` (filtered by extension).
4. For each image:
   - Load with Pillow and apply the CLIP preprocessing.
   - Encode into an image embedding.
   - Compute cosine similarity against every category embedding.
   - Pick the category with the highest similarity; if it is below `similarity_min`, the image becomes `uncategorized`.
   - Build the destination path (`--dst` + category id + optional preserved subpath).
   - Move/copy files or just print actions if in `dry-run` mode.

---

## 8. Tips & extensions

- **Speed optimization**:
  - Use `--max-images` to quickly test config/category behavior before running on the full dataset.
  - Later you can implement image batching to better leverage PyTorch’s vectorization.
- **Tuning categories**:
  - If many images are misclassified:
    - Refine or add prompts with clearer descriptions.
    - Adjust `similarity_min`.
    - Split broad categories into 2–3 more specific ones.
- **GPU (optional)**:
  - If your machine has a GPU, you can set in `config.yaml`:
    ```yaml
    model:
      name: "ViT-B-32"
      pretrained: "laion2b_s34b_b79k"
      device: "cuda"
    ```
  - If not, leave it as `cpu` (default).

---

## 9. Current limitations

- No detailed CSV/JSON logging yet (file → category, score). This can be added later.
- No GUI; only a CLI interface for now.

If you want CSV logging of classification results or a helper script to **revert** / change categories after running, those can be added as next steps.