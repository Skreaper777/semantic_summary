import os
import re
import sys
import argparse

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

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

def extract_semantic_structure(root_path, output_file="semantic_summary.txt", copy_to_clipboard=False):
    summary = []

    current_script_path = os.path.abspath(sys.argv[0])

    for dirpath, dirnames, filenames in os.walk(root_path):
        # 🧼 Пропускаем скрытые папки
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        rel_dir = os.path.relpath(dirpath, root_path)
        if rel_dir == ".":
            rel_dir = "[корень проекта]"
        summary.append(f"\n📁 Папка: {rel_dir}")

        for filename in sorted(filenames):
            if filename.endswith(".py"):
                file_path = os.path.join(dirpath, filename)

                # ⛔ Пропускаем сам скрипт
                if os.path.abspath(file_path) == current_script_path:
                    continue

                summary.append(f"\n  📄 Файл: {filename}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    inside_function = False
                    function_indent = None
                    function_variables = []

                    semantic_headings = []

                    for i, line in enumerate(lines):
                        stripped = line.strip()

                        # Сбор структурных элементов
                        if is_relevant_line(line):
                            semantic_headings.append(stripped)

                        # Обработка функций и локальных переменных
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

                    if semantic_headings:
                        summary.extend([f"    {line}" for line in semantic_headings])
                    elif not inside_function:
                        summary.append("    ⚠️ Нет структурных элементов (import/class/def/const)")

                except Exception as e:
                    summary.append(f"    ⚠️ Ошибка при чтении: {e}")

    result = "\n".join(summary)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

    if copy_to_clipboard and CLIPBOARD_AVAILABLE:
        pyperclip.copy(result)
        print("📋 Сводка скопирована в буфер обмена.")

    print(f"✅ Структура проекта сохранена в: {output_file}")

# 🚀 CLI-запуск
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Генерация семантической сводки Python-проекта.")
    parser.add_argument("--path", type=str, default=".", help="Путь к папке проекта")
    parser.add_argument("--copy", action="store_true", help="Копировать результат в буфер обмена")

    args = parser.parse_args()
    root_path = os.path.abspath(args.path)

    extract_semantic_structure(root_path, copy_to_clipboard=args.copy)
