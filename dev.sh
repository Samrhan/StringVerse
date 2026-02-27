#!/bin/bash
set -e

echo "=== StringVerse Dev Mode ==="

# Build WASM first
echo "Building WASM..."
cd wasm
wasm-pack build --target web --out-dir ../frontend/src/wasm-pkg --dev
cd ..

echo "Starting Vite dev server..."
cd frontend
npm install
npm run dev
