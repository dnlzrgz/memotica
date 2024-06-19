clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✨ Clean up complete!"

format:
	@echo "🔍 Formatting..."
	ruff check . --fix
	@echo "✨ Format complete!"

run:
	@echo "🚀 Starting development..."
	@export ENVIRONMENT=development && poetry run memotica

dev:
	@echo "🚀 Starting development..."
	@export ENVIRONMENT=development && textual run src/memotica/tui.py --dev

console:
	@echo "🚀 Starting development console..."
	textual console -v
