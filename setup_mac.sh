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
APP_PATH="$HOME/Desktop/Reel Studio.app"
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Creating 'Reel Studio.app' on your Desktop..."
mkdir -p "$APP_PATH/Contents/MacOS"

# Write launcher shell script inside the App
cat << EOF > "$APP_PATH/Contents/MacOS/BFPReelStudio"
#!/bin/bash
export PATH="/opt/homebrew/bin:/usr/local/bin:\$PATH"
cd "$PROJECT_DIR"
python3 app.py
EOF

# Make app script executable
chmod +x "$APP_PATH/Contents/MacOS/BFPReelStudio"

echo "All done! Double-click 'Reel Studio' on your Desktop to run."