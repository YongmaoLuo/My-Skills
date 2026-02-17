#!/bin/bash
# Skill Installation Script
# Installs the skill-creating skill to various agent environments

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_NAME="skill-creating"

echo "Skill Creating - Installation Script"
echo "=================================="
echo

# Function to install to a specific path
install_skill() {
    local target_dir=$1
    local agent_name=$2
    
    # Create target directory if it doesn't exist
    if [ ! -d "$target_dir" ]; then
        echo "Creating directory: $target_dir"
        mkdir -p "$target_dir"
    fi
    
    # Check if skill already exists
    if [ -d "$target_dir/$SKILL_NAME" ]; then
        read -p "Skill already exists in $agent_name. Overwrite? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipping $agent_name installation."
            return
        fi
        rm -rf "$target_dir/$SKILL_NAME"
    fi
    
    # Copy skill
    echo "Installing to $agent_name..."
    cp -r "$SCRIPT_DIR" "$target_dir/$SKILL_NAME"
    echo "✓ Installed to $agent_name"
    echo
}

# Detect shell
detect_shell() {
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
    else
        SHELL_CONFIG="$HOME/.profile"
    fi
}

# Menu for installation
echo "Select agent(s) to install skill-creating:"
echo "1) Claude Code (~/.claude/skills/)"
echo "2) Cursor (~/.cursor/skills/)"
echo "3) OpenCode (~/.opencode/skills/)"
echo "4) All of the above"
echo "5) Custom path"
echo "6) List only (don't install)"
echo
read -p "Enter choice (1-6): " choice

case $choice in
    1)
        install_skill "$HOME/.claude/skills" "Claude Code"
        ;;
    2)
        install_skill "$HOME/.cursor/skills" "Cursor"
        ;;
    3)
        install_skill "$HOME/.opencode/skills" "OpenCode"
        ;;
    4)
        install_skill "$HOME/.claude/skills" "Claude Code"
        install_skill "$HOME/.cursor/skills" "Cursor"
        install_skill "$HOME/.opencode/skills" "OpenCode"
        ;;
    5)
        read -p "Enter custom installation path: " custom_path
        if [ -n "$custom_path" ]; then
            install_skill "$custom_path" "Custom"
        fi
        ;;
    6)
        echo "Installation paths for reference:"
        echo "  Claude Code: $HOME/.claude/skills/"
        echo "  Cursor: $HOME/.cursor/skills/"
        echo "  OpenCode: $HOME/.opencode/skills/"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo "Installation complete!"
echo
echo "To validate skills, you can use the included validation script:"
echo "  python3 $SCRIPT_DIR/scripts/validate_skill.py <skill-path>"
echo
echo "For more information, see:"
echo "  - Quick Start: $SCRIPT_DIR/references/QUICK_START.md"
echo "  Technical Reference: $SCRIPT_DIR/references/TECHNICAL_REFERENCE.md"
echo "  Skill Template: $SCRIPT_DIR/assets/templates/SKILL_TEMPLATE.md"
