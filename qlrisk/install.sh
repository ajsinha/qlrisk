#!/bin/bash
# QLRisk v1.0.0 - Installation Script
# Copyright © 2025-2030, Ashutosh Sinha | Email: ajsinha@gmail.com

echo "=========================================="
echo " QLRisk v1.0.0 Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "ERROR: Python 3.9+ required"; exit 1; }

# Install dependencies
echo ""
echo "Installing required packages..."
pip install numpy scipy --quiet

# Optional: Install QuantLib
echo ""
echo "Installing QuantLib (optional)..."
pip install QuantLib --quiet 2>/dev/null || echo "Note: QuantLib not available - using Python implementations"

echo ""
echo "=========================================="
echo " Installation Complete!"
echo "=========================================="
echo ""
echo "Quick start:"
echo "  python qlrisk/main.py --quick"
echo ""
echo "Full demo:"
echo "  python qlrisk/main.py"
echo ""
echo "Run benchmarks:"
echo "  python qlrisk/main.py --benchmark"
echo ""
