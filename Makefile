clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✨ Clean up complete!"

format:
	@echo "🔍 Formatting..."
	ruff check . --fix
	@echo "✨ Format complete!"

dev:
	@echo "🚀 Starting development..."
	textual run --dev src/memotica/tui.py

console:
	@echo "🚀 Starting development console..."
	textual console -v
