#!/usr/bin/env python3
"""
Установочный скрипт для CachyOS + Niri + Noctalia
Использование: ./install.py [-y]
  -y  Автоматически подтверждать все шаги
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

HOME = Path.home()
CONFIG_DIR = HOME / ".config"
SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_CONFIGS = SCRIPT_DIR / "configs"
REPO_ROOT = SCRIPT_DIR

# Директории назначения для конфигов (сопоставление: имя в репо -> имя в ~/.config)
CONFIG_MAPPING = {
    "niri": "niri",
    "noctalia": "noctalia",
    "alacritty": "alacritty",
    "fastfetch": "fastfetch",
}

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def log(msg: str, level: str = "INFO"):
    """Вывод сообщения с префиксом уровня."""
    prefixes = {
        "INFO": "[INFO]",
        "WARN": "[WARN]",
        "ERROR": "[ERROR]",
        "STEP": "\n>>>",
        "OK": "[OK]",
    }
    prefix = prefixes.get(level, "[?]")
    print(f"{prefix} {msg}")


def confirm(prompt: str, auto_yes: bool = False) -> bool:
    """Запрос подтверждения с поддержкой автоответа."""
    if auto_yes:
        log(f"{prompt} — автоматически подтверждено (-y)", "OK")
        return True
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
        return answer in ("y", "yes", "да")
    except (KeyboardInterrupt, EOFError):
        print()
        return False


def run_command(cmd: str | list, check: bool = True, cwd: Path | None = None,
                shell: bool = False, auto_yes: bool = False) -> subprocess.CompletedProcess:
    """Запуск команды с логированием."""
    if isinstance(cmd, str) and not shell:
        cmd = cmd.split()
    log(f"Выполняется: {' '.join(cmd) if isinstance(cmd, list) else cmd}", "INFO")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            cwd=cwd,
            shell=shell,
            text=True,
            capture_output=False,
        )
        return result
    except subprocess.CalledProcessError as e:
        log(f"Команда завершилась с ошибкой (код {e.returncode})", "ERROR")
        raise
    except FileNotFoundError:
        log(f"Команда не найдена: {cmd[0] if isinstance(cmd, list) else cmd}", "ERROR")
        raise


# ============================================================
# ШАГ 0: Установка Python (если его нет)
# ============================================================

def step_0_install_python(auto_yes: bool):
    """Шаг 0: Проверка и установка Python через репозитории CachyOS."""
    log("ШАГ 0: Проверка наличия Python", "STEP")

    if shutil.which("python3"):
        version = subprocess.run(
            ["python3", "--version"], capture_output=True, text=True
        ).stdout.strip()
        log(f"Python уже установлен: {version}", "OK")
        return

    if not confirm("Python не найден. Установить python из репозиториев CachyOS?", auto_yes):
        log("Пропущен шаг установки Python.", "WARN")
        return

    run_command(["sudo", "pacman", "-S", "--noconfirm", "python"], auto_yes=auto_yes)
    log("Python установлен.", "OK")


# ============================================================
# ШАГ 1: Установка запрета и tg-ws-proxy
# ============================================================

def step_1_zapret_and_tgwsproxy(auto_yes: bool):
    """Шаг 1: Установка zapret и tg-ws-proxy."""
    log("ШАГ 1: Установка zapret и tg-ws-proxy", "STEP")

    # 1a. Zapret
    if confirm("Установить zapret (обход замедления YouTube/Discord)?", auto_yes):
        log("Клонирование репозитория zapret...", "INFO")
        zapret_dir = REPO_ROOT / "zapret-discord-youtube"
        if zapret_dir.exists():
            shutil.rmtree(zapret_dir)
        run_command(
            ["git", "clone", "https://github.com/kartavkun/zapret-discord-youtube.git"],
            cwd=REPO_ROOT,
            auto_yes=auto_yes,
        )
        log("Запуск установки zapret...", "INFO")
        run_command(
            "bash main_script.sh",
            cwd=zapret_dir,
            shell=True,
            auto_yes=auto_yes,
        )
        log("Zapret установлен.", "OK")
    else:
        log("Пропущена установка zapret.", "WARN")

    # 1b. tg-ws-proxy
    if confirm("Установить tg-ws-proxy-bin (MTProto proxy для Telegram)?", auto_yes):
        log("Клонирование tg-ws-proxy-bin из AUR...", "INFO")
        tgws_dir = REPO_ROOT / "tg-ws-proxy-bin"
        if tgws_dir.exists():
            shutil.rmtree(tgws_dir)
        run_command(
            ["git", "clone", "https://aur.archlinux.org/tg-ws-proxy-bin.git"],
            cwd=REPO_ROOT,
            auto_yes=auto_yes,
        )
        log("Сборка и установка tg-ws-proxy-bin...", "INFO")
        # Используем --skipchecksums, т.к. AUR-пакет имеет известную проблему с хэшами [citation:9]
        run_command(
            ["makepkg", "-si", "--noconfirm", "--skipchecksums"],
            cwd=tgws_dir,
            auto_yes=auto_yes,
        )
        log("tg-ws-proxy-bin установлен.", "OK")
    else:
        log("Пропущена установка tg-ws-proxy-bin.", "WARN")


# ============================================================
# ШАГ 2-4: Копирование конфигов
# ============================================================

def copy_config(config_name: str, auto_yes: bool):
    """Копирование конфига из репозитория в ~/.config."""
    src = REPO_CONFIGS / config_name
    if not src.exists():
        log(f"Директория конфига {config_name} не найдена в {src}", "WARN")
        return

    dst_name = CONFIG_MAPPING.get(config_name, config_name)
    dst = CONFIG_DIR / dst_name

    if not confirm(f"Скопировать конфиг {config_name} в {dst}?", auto_yes):
        log(f"Пропущено копирование {config_name}.", "WARN")
        return

    # Создаём родительскую директорию
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Копируем с заменой
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    log(f"Конфиг {config_name} скопирован в {dst}", "OK")


def step_2_niri_config(auto_yes: bool):
    log("ШАГ 2: Копирование конфига Niri", "STEP")
    copy_config("niri", auto_yes)


def step_3_noctalia_config(auto_yes: bool):
    log("ШАГ 3: Копирование конфига Noctalia", "STEP")
    copy_config("noctalia", auto_yes)


def step_4_alacritty_config(auto_yes: bool):
    log("ШАГ 4: Копирование конфига Alacritty", "STEP")
    copy_config("alacritty", auto_yes)


# ============================================================
# ШАГ 5: Fastfetch
# ============================================================

def step_5_fastfetch(auto_yes: bool):
    log("ШАГ 5: Генерация и копирование конфига Fastfetch", "STEP")

    if not confirm("Сгенерировать конфиг fastfetch и заменить на свой?", auto_yes):
        log("Пропущен шаг fastfetch.", "WARN")
        return

    # Генерация стандартного конфига (если fastfetch установлен)
    if shutil.which("fastfetch"):
        run_command(["fastfetch", "--gen-config"], auto_yes=auto_yes)
        log("Стандартный конфиг fastfetch сгенерирован.", "INFO")
    else:
        log("fastfetch не найден, пропускаем генерацию.", "WARN")

    copy_config("fastfetch", auto_yes)


# ============================================================
# ШАГ 6: Подключение ChaoticAUR
# ============================================================

def step_6_chaotic_aur(auto_yes: bool):
    log("ШАГ 6: Подключение ChaoticAUR (с низким приоритетом)", "STEP")

    if not confirm("Подключить репозиторий ChaoticAUR?", auto_yes):
        log("Пропущено подключение ChaoticAUR.", "WARN")
        return

    pacman_conf = Path("/etc/pacman.conf")

    # Проверяем, не подключён ли уже
    content = pacman_conf.read_text()
    if "[chaotic-aur]" in content:
        log("ChaoticAUR уже подключён в pacman.conf", "OK")
        return

    # Установка ключей и mirrorlist через pacman
    log("Установка chaotic-keyring и chaotic-mirrorlist...", "INFO")
    run_command(
        ["sudo", "pacman", "-S", "--noconfirm", "chaotic-keyring", "chaotic-mirrorlist"],
        auto_yes=auto_yes,
    )

    # Добавление в конец pacman.conf (низкий приоритет)
    # ChaoticAUR будет последним в списке, поэтому оф. репозитории CachyOS имеют приоритет
    chaotic_block = "\n[chaotic-aur]\nInclude = /etc/pacman.d/chaotic-mirrorlist\n"

    log("Добавление ChaoticAUR в конец /etc/pacman.conf...", "INFO")
    # Используем tee через sudo для добавления
    run_command(
        f"echo '{chaotic_block}' | sudo tee -a /etc/pacman.conf",
        shell=True,
        auto_yes=auto_yes,
    )

    log("ChaoticAUR подключён (низкий приоритет).", "OK")


# ============================================================
# ШАГ 7: Установка пакетов
# ============================================================

PACKAGES = [
    # GUI приложения
    # GUI-приложения
    "clash-verge-rev", "code", "docker", "droidcam-obs-plugin",
    "flatpak", "krita", "lact", "mpv", "mpvpaper", "nwg-look",
    "obsidian", "obs-studio", "opentabletdriver", "prismlauncher",
    "protonplus", "shelly", "steam", "telegram-desktop",
    "vesktop-bin",

    # Консольные утилиты
    "tree", "ipset", "ntfs-3g", "tg-ws-proxy-bin", "yt-dlp",

    # Ключи и зеркала
    "archlinux-keyring", "cachyos-keyring",
    "cachyos-plymouth-bootanimation", "cachyos-plymouth-theme",
    "chaotic-keyring", "chaotic-mirrorlist",

    # Захват экрана / OCR (базовое)
    "grim", "slurp", "wf-recorder", "xclip", "tesseract",
    "tesseract-data-eng", "tesseract-data-rus", "zbar", "ffmpeg",

    # Screen Toolkit (Noctalia plugin) — дополнительные зависимости
    "imagemagick", "curl", "jq", "bc", "xdg-utils",
    "gpu-screen-recorder", "satty",

    # Сборка Aseprite
    "clang", "cmake", "ninja", "gcc", "fontconfig", "mesa",
    "libx11", "libxcursor", "libxi", "libxrandr", "libwebp",

    # Прочее
    "uv",
]


def step_7_install_packages(auto_yes: bool):
    log("ШАГ 7: Установка пакетов из репозиториев", "STEP")

    if not confirm(f"Установить {len(PACKAGES)} пакетов?", auto_yes):
        log("Пропущена установка пакетов.", "WARN")
        return

    # Сначала обновляем базы
    run_command(["sudo", "pacman", "-Sy"], auto_yes=auto_yes)

    # Устанавливаем пакеты
    # Часть пакетов может быть в AUR (vesktop-bin, tg-ws-proxy-bin)
    # Используем paru, который предустановлен в CachyOS [citation:3]
    native_packages = []
    aur_packages = ["vesktop-bin", "tg-ws-proxy-bin"]

    for pkg in PACKAGES:
        if pkg not in aur_packages:
            native_packages.append(pkg)

    # Установка нативных пакетов через pacman
    if native_packages:
        log("Установка нативных пакетов через pacman...", "INFO")
        # Разбиваем на чанки, чтобы не превысить лимит аргументов
        chunk_size = 20
        for i in range(0, len(native_packages), chunk_size):
            chunk = native_packages[i:i + chunk_size]
            run_command(
                ["sudo", "pacman", "-S", "--noconfirm", "--needed"] + chunk,
                auto_yes=auto_yes,
            )

    # Установка AUR-пакетов через paru (если есть)
    if aur_packages:
        if shutil.which("paru"):
            log("Установка AUR-пакетов через paru...", "INFO")
            run_command(
                ["paru", "-S", "--noconfirm", "--needed", "--skipchecksums"] + aur_packages,
                auto_yes=auto_yes,
            )
        else:
            log("paru не найден. Пропускаем AUR-пакеты.", "WARN")

    log("Пакеты установлены.", "OK")


# ============================================================
# ШАГ 8: Установка VS Code из Flatpak
# ============================================================

def step_8_vscode_flatpak(auto_yes: bool):
    log("ШАГ 8: Установка VS Code (проприетарная версия) из Flatpak", "STEP")

    if not confirm("Установить VS Code из Flatpak?", auto_yes):
        log("Пропущена установка VS Code.", "WARN")
        return

    # Добавляем репозиторий Flathub, если его нет
    run_command(
        ["flatpak", "remote-add", "--if-not-exists", "flathub",
         "https://flathub.org/repo/flathub.flatpakrepo"],
        auto_yes=auto_yes,
    )

    # Устанавливаем VS Code
    run_command(
        ["flatpak", "install", "-y", "flathub", "com.visualstudio.code"],
        auto_yes=auto_yes,
    )

    log("VS Code установлен из Flatpak.", "OK")


# ============================================================
# ШАГ 9: Клонирование и сборка репозиториев
# ============================================================

def step_9_build_repos(auto_yes: bool):
    log("ШАГ 9: Клонирование и сборка ShotX, WhiteSur, Aseprite", "STEP")

    # 9a. ShotX
    if confirm("Клонировать и собрать ShotX?", auto_yes):
        shotx_dir = REPO_ROOT / "ShotX"
        if shotx_dir.exists():
            shutil.rmtree(shotx_dir)
        run_command(
            ["git", "clone", "https://github.com/vedesh-padal/ShotX.git"],
            cwd=REPO_ROOT,
            auto_yes=auto_yes,
        )
        log("ShotX клонирован. Зависимости для сборки уже установлены на шаге 7.", "OK")
    else:
        log("Пропущен ShotX.", "WARN")

    # 9b. WhiteSur
    if confirm("Клонировать WhiteSur (иконки)?", auto_yes):
        whitesur_dir = REPO_ROOT / "WhiteSur-icon-theme"
        if whitesur_dir.exists():
            shutil.rmtree(whitesur_dir)
        run_command(
            ["git", "clone", "https://github.com/vinceliuice/WhiteSur-icon-theme.git"],
            cwd=REPO_ROOT,
            auto_yes=auto_yes,
        )
        log("WhiteSur клонирован.", "OK")
    else:
        log("Пропущен WhiteSur.", "WARN")

    # 9c. Aseprite
    if confirm("Клонировать и собрать Aseprite?", auto_yes):
        aseprite_dir = REPO_ROOT / "aseprite"
        if aseprite_dir.exists():
            shutil.rmtree(aseprite_dir)
        run_command(
            ["git", "clone", "--recursive",
             "https://github.com/aseprite/aseprite.git", str(aseprite_dir)],
            cwd=REPO_ROOT,
            auto_yes=auto_yes,
        )
        # Создаём директорию сборки
        build_dir = aseprite_dir / "build"
        build_dir.mkdir(exist_ok=True)

        log("Конфигурация сборки Aseprite через CMake...", "INFO")
        run_command(
            ["cmake", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
             "-DLAF_UPDATE_INFO=OFF", ".."],
            cwd=build_dir,
            auto_yes=auto_yes,
        )

        log("Сборка Aseprite (это может занять длительное время)...", "INFO")
        run_command(
            ["ninja", "aseprite"],
            cwd=build_dir,
            auto_yes=auto_yes,
        )
        log("Aseprite собран.", "OK")
    else:
        log("Пропущен Aseprite.", "WARN")


# ============================================================
# ШАГ 10: Симлинки и .desktop для Aseprite
# ============================================================

def step_10_aseprite_links(auto_yes: bool):
    log("ШАГ 10: Создание симлинков и .desktop для Aseprite", "STEP")

    aseprite_bin = REPO_ROOT / "aseprite" / "build" / "bin" / "aseprite"
    if not aseprite_bin.exists():
        log("Бинарник Aseprite не найден. Пропускаем.", "WARN")
        return

    if not confirm("Создать симлинк и .desktop для Aseprite?", auto_yes):
        log("Пропущено создание ссылок.", "WARN")
        return

    # Симлинк в ~/.local/bin
    local_bin = HOME / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)
    link_path = local_bin / "aseprite"

    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    link_path.symlink_to(aseprite_bin)
    log(f"Создан симлинк: {link_path} -> {aseprite_bin}", "OK")

    # .desktop файл
    desktop_dir = HOME / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "aseprite.desktop"

    desktop_content = f"""[Desktop Entry]
Type=Application
Name=Aseprite
Comment=Animated sprite editor & pixel art tool
Exec={link_path} %F
Icon=aseprite
Terminal=false
Categories=Graphics;2DGraphics;RasterGraphics;
MimeType=image/bmp;image/gif;image/jpeg;image/png;image/x-aseprite;
"""
    desktop_file.write_text(desktop_content)
    log(f"Создан .desktop файл: {desktop_file}", "OK")


# ============================================================
# ШАГ 11: Удаление локальных репозиториев (кроме zapret)
# ============================================================

def step_11_cleanup(auto_yes: bool):
    log("ШАГ 11: Удаление локальных репозиториев (кроме zapret)", "STEP")

    if not confirm("Удалить временные репозитории (кроме zapret)?", auto_yes):
        log("Пропущена очистка.", "WARN")
        return

    keep_dirs = {"zapret-discord-youtube", "configs", ".git"}
    # Также сохраняем сам install.py и README
    keep_files = {"install.py", "README.md", ".gitignore"}

    for item in REPO_ROOT.iterdir():
        if item.name in keep_dirs or item.name in keep_files:
            continue
        if item.is_dir():
            log(f"Удаление директории: {item}", "INFO")
            shutil.rmtree(item)
        elif item.is_file():
            log(f"Удаление файла: {item}", "INFO")
            item.unlink()

    log("Очистка завершена.", "OK")


# ============================================================
# ШАГ 12: Перевод времени на RTC
# ============================================================

def step_12_rtc_time(auto_yes: bool):
    log("ШАГ 12: Перевод системного времени на локальное RTC", "STEP")

    if not confirm("Установить локальное время RTC (для двойной загрузки с Windows)?", auto_yes):
        log("Пропущен перевод времени.", "WARN")
        return

    run_command(
        ["sudo", "timedatectl", "set-local-rtc", "1", "--adjust-system-clock"],
        auto_yes=auto_yes,
    )
    log("Время переведено на локальное RTC.", "OK")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Установочный скрипт CachyOS + Niri + Noctalia"
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Автоматически подтверждать все шаги (без интерактивного ввода)",
    )
    args = parser.parse_args()
    auto_yes = args.yes

    log("=" * 60, "INFO")
    log("Установка CachyOS + Niri + Noctalia", "INFO")
    log("=" * 60, "INFO")
    if auto_yes:
        log("Режим -y: все шаги будут выполнены автоматически.", "WARN")

    steps = [
        ("0. Проверка Python", step_0_install_python),
        ("1. Установка zapret и tg-ws-proxy", step_1_zapret_and_tgwsproxy),
        ("2. Копирование конфига Niri", step_2_niri_config),
        ("3. Копирование конфига Noctalia", step_3_noctalia_config),
        ("4. Копирование конфига Alacritty", step_4_alacritty_config),
        ("5. Генерация Fastfetch", step_5_fastfetch),
        ("6. Подключение ChaoticAUR", step_6_chaotic_aur),
        ("7. Установка пакетов", step_7_install_packages),
        ("8. Установка VS Code (Flatpak)", step_8_vscode_flatpak),
        ("9. Сборка ShotX, WhiteSur, Aseprite", step_9_build_repos),
        ("10. Ссылки для Aseprite", step_10_aseprite_links),
        ("11. Очистка репозиториев", step_11_cleanup),
        ("12. Перевод времени на RTC", step_12_rtc_time),
    ]

    for step_name, step_func in steps:
        try:
            step_func(auto_yes)
        except subprocess.CalledProcessError as e:
            log(f"Шаг '{step_name}' завершился с ошибкой: {e}", "ERROR")
            if not confirm(f"Продолжить выполнение после ошибки в шаге '{step_name}'?", auto_yes):
                log("Установка прервана пользователем.", "ERROR")
                sys.exit(1)
        except Exception as e:
            log(f"Неожиданная ошибка в шаге '{step_name}': {e}", "ERROR")
            if not confirm(f"Продолжить выполнение после ошибки?", auto_yes):
                sys.exit(1)

    log("=" * 60, "OK")
    log("Установка завершена успешно!", "OK")
    log("=" * 60, "OK")


if __name__ == "__main__":
    main()