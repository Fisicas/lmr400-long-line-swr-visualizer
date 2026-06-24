# Release Instructions

This project is designed so radio-club members can either run the Python source or download a Windows executable from GitHub Releases.

## One-time repository setup

1. Create a new public repository on GitHub named:

   ```text
   lmr400-long-line-swr-visualizer
   ```

2. Clone the empty repository locally:

   ```bash
   git clone https://github.com/nelsondirect/lmr400-long-line-swr-visualizer.git
   cd lmr400-long-line-swr-visualizer
   ```

3. Copy the prepared project files into the cloned folder.

4. Commit and push:

   ```bash
   git add .
   git commit -m "Initial LMR-400 long-line SWR visualizer"
   git push -u origin main
   ```

## Create the first release

Create and push a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The included GitHub Actions workflow will build the Windows executable and attach it to a GitHub Release.

## Manual executable build

On a Windows machine with Python installed:

```bash
python -m pip install -r requirements-dev.txt
pyinstaller --onefile --windowed --name LMR400_Long_Line_SWR_Visualizer lmr400_long_line_swr_visualizer.py
```

The `.exe` will appear in:

```text
dist/LMR400_Long_Line_SWR_Visualizer.exe
```

Upload that file to the GitHub Release if you do not want to use GitHub Actions.

## Recommended release notes for v0.1.0

```markdown
# LMR-400 Long-Line SWR Visualizer v0.1.0

Initial public release for radio-club demonstration and testing.

Includes:

- Datasheet practical model for LMR-400 apparent SWR.
- Physical RLCG transmission-line model.
- Open, short, and custom-load terminations.
- Plots of apparent SWR, one-way loss, input impedance, and complex reflection coefficient.
- CSV export and figure export.
- Technical note explaining why a long open-ended feedline can show moderate apparent SWR.
```
