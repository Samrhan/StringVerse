#!/bin/bash
set -e

echo "=== StringVerse: Rust/WASM + React Build ==="

# 1. Build WASM from Rust
echo ""
echo "--- Building Rust → WASM ---"
cd wasm
wasm-pack build --target web --out-dir ../frontend/src/wasm-pkg
cd ..

# 2. Install frontend deps
echo ""
echo "--- Installing frontend dependencies ---"
cd frontend
npm install

# 3. Build frontend
echo ""
echo "--- Building React frontend ---"
npm run build
cd ..

echo ""
echo "=== Build complete! ==="
echo "Run: cd frontend && npm run preview"
echo "Or open: frontend/dist/index.html"
