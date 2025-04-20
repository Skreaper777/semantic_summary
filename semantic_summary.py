import os
import re
import sys

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

def extract_semantic_structure(root_path, output_file="semantic_summary.txt"):
    summary = []

    def is_relevant_line(line):
        stripped = line.strip()
        return (
            stripped.startswith("import ")
            or stripped.startswith("from ")
            or re.match(r"^class\s+\w+", stripped)
            or re.match(r"^def\s+\w+", stripped)
            or re.match(r"^[A-Z_]+\s*=", stripped)  # CONSTANTS
            or stripped.startswith("@")
        )

    for dirpath, dirnames, filenames in os.walk(root_path):
        # 🧼 Пропускаем скрытые папки
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        rel_dir = os.path.relpath(dirpath, root_path)
        if rel_dir == ".":
            rel_dir = "[корень проекта]"
        summary.append(f"\n📁 Папка: {rel_dir}")

        for filename in filenames:
            if filename.endswith(".py"):
                file_path = os.path.join(dirpath, filename)
                summary.append(f"\n  📄 Файл: {filename}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                        inside_function = False
                        function_indent = None
                        function_variables = []

                        for i, line in enumerate(lines):
                            stripped = line.strip()

                            if re.match(r"^def\s+\w+", stripped):
                                if function_variables:
                                    summary.append("    🔸 Локальные переменные:")
                                    summary.extend([f"      - {var}" for var in function_variables])
                                    function_variables = []

                                summary.append(f"    {stripped}")
                                inside_function = True
                                function_indent = len(line) - len(line.lstrip())
                                continue

                            if inside_function:
                                current_indent = len(line) - len(line.lstrip())
                                if current_indent <= function_indent:
                                    if function_variables:
                                        summary.append("    🔸 Локальные переменные:")
                                        summary.extend([f"      - {var}" for var in function_variables])
                                    inside_function = False
                                    function_variables = []
                                else:
                                    if "=" in line and not stripped.startswith("#"):
                                        left = line.split("=")[0].strip()
                                        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", left):
                                            function_variables.append(left)

                        if function_variables:
                            summary.append("    🔸 Локальные переменные:")
                            summary.extend([f"      - {var}" for var in function_variables])

                        # Импорты, классы, константы и декораторы
                        semantic_headings = [line.rstrip() for line in lines if is_relevant_line(line)]
                        if semantic_headings:
                            summary.extend([f"    {line}" for line in semantic_headings])
                        else:
                            summary.append("    ⚠️ Нет структурных элементов (import/class/def/const)")
                except Exception as e:
                    summary.append(f"    ⚠️ Ошибка при чтении: {e}")

    result = "\n".join(summary)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

    if CLIPBOARD_AVAILABLE:
        pyperclip.copy(result)
        print("📋 Сводка скопирована в буфер обмена.")

    print(f"✅ Структура проекта сохранена в: {output_file}")

# 🚀 Запуск
if __name__ == "__main__":
    root = os.path.dirname(os.path.abspath(__file__))
    extract_semantic_structure(root)
