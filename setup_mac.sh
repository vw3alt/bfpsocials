#!/bin/bash
echo "Setup on mac..."

# 1. Install Homebrew if missing
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Ensure brew path is loaded
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 2. Install FFmpeg & Python Dependencies
echo "Installing FFmpeg and Python libraries..."
brew install ffmpeg
pip3 install moviepy proglog

# 3. Build the double-clickable Mac App Bundle on Desktop
APP_PATH="$HOME/Desktop/BFP Reel Studio.app"
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Creating 'BFP Reel Studio.app' on your Desktop..."
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# 4. Convert bfpfilm.png to Mac .icns Icon (if present)
if [ -f "$PROJECT_DIR/bfpfilm.png" ]; then
    echo "Converting custom icon..."
    ICONSET_DIR="$PROJECT_DIR/icon.iconset"
    mkdir -p "$ICONSET_DIR"
    
    # Generate various sizes required for a valid Mac icon set
    sips -z 16 16 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null 2>&1
    sips -z 32 32 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null 2>&1
    sips -z 32 32 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null 2>&1
    sips -z 64 64 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null 2>&1
    sips -z 128 128 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null 2>&1
    sips -z 256 256 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null 2>&1
    sips -z 256 256 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null 2>&1
    sips -z 512 512 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null 2>&1
    sips -z 512 512 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null 2>&1
    sips -z 1024 1024 "$PROJECT_DIR/bfpfilm.png" --out "$ICONSET_DIR/icon_512x512@2x.png" >/dev/null 2>&1
    
    # Bundle into .icns and clean up temp folder
    iconutil -c icns "$ICONSET_DIR" -o "$APP_PATH/Contents/Resources/app_icon.icns"
    rm -rf "$ICONSET_DIR"
    
    # Write Info.plist telling macOS to use the new icon and correct executable name
    cat << EOF > "$APP_PATH/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>BFPReelStudio</string>
    <key>CFBundleIconFile</key>
    <string>app_icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.bfp.reelstudio</string>
    <key>CFBundleName</key>
    <string>BFP Reel Studio</string>
</dict>
</plist>
EOF
fi

# Write launcher shell script inside the App
cat << EOF > "$APP_PATH/Contents/MacOS/BFPReelStudio"
#!/bin/bash
export PATH="/opt/homebrew/bin:/usr/local/bin:\$PATH"
cd "$PROJECT_DIR"
python3 app.py
EOF

# Make app script executable (matching the filename without spaces)
chmod +x "$APP_PATH/Contents/MacOS/BFPReelStudio"

echo "All done! Double-click 'BFP Reel Studio' on your Desktop to run."