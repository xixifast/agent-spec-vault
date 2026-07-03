#!/usr/bin/env bash
set -eu

PACKAGE_SPEC="${PACKAGE_SPEC:-agent-spec-vault}"
SOURCE_PACKAGE_SPEC="${SOURCE_PACKAGE_SPEC:-git+https://github.com/xixifast/agent-spec-vault.git}"
APP_HOME="${APP_HOME:-"$HOME/.local/share/agent-spec-vault"}"
BIN_DIR="${BIN_DIR:-"$HOME/.local/bin"}"
VENV_DIR="$APP_HOME/venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "agent-spec-vault requires python3." >&2
  exit 1
fi

if command -v pipx >/dev/null 2>&1; then
  echo "Installing agent-spec-vault with pipx..."
  if ! pipx install --force "$PACKAGE_SPEC"; then
    if [ "$PACKAGE_SPEC" = "$SOURCE_PACKAGE_SPEC" ]; then
      exit 1
    fi
    echo "PyPI install failed; falling back to the GitHub source package..."
    pipx install --force "$SOURCE_PACKAGE_SPEC"
  fi
  if command -v specv >/dev/null 2>&1; then
    specv init
  elif [ -x "$BIN_DIR/specv" ]; then
    "$BIN_DIR/specv" init
  else
    echo "Installed with pipx. Open a new shell or run: pipx ensurepath"
    echo "Then initialize the vault with: specv init"
  fi
  exit 0
fi

echo "pipx was not found; installing into a private virtual environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null
if ! "$VENV_DIR/bin/python" -m pip install --upgrade "$PACKAGE_SPEC"; then
  if [ "$PACKAGE_SPEC" = "$SOURCE_PACKAGE_SPEC" ]; then
    exit 1
  fi
  echo "PyPI install failed; falling back to the GitHub source package..."
  "$VENV_DIR/bin/python" -m pip install --upgrade "$SOURCE_PACKAGE_SPEC"
fi
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/specv" "$BIN_DIR/specv"
"$VENV_DIR/bin/specv" init

echo "agent-spec-vault installed."
echo "If 'specv' is not found, add this to PATH: $BIN_DIR"
