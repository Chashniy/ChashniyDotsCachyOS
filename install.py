#!/bin/sh
""":"
if ! command -v python3 >/dev/null 2>&1; then
    case " $* " in
        *" -y "*|*" --yes "*)
            AUTO=1
            ;;
        *)
            AUTO=0
            ;;
    esac

    if [ "$AUTO" -ne 1 ]; then
        printf "Python не найден. Установить python через pacman? [y/N]: "
        read answer

        case "$answer" in
            y|Y|yes|YES|д|Д|да|Да)
                ;;
            *)
                exit 0
                ;;
        esac
    fi

    sudo pacman -Syu --needed python || exit $?
fi

exec python3 "$0" "$@"
exit $?
":"""

import os
import sys

# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------

import argparse
import shutil
import subprocess
import time
from pathlib import Path


# ===========================================================================
# PATHS
# ===========================================================================

HOME = Path.home()
CONFIG_DIR = HOME / ".config"
SCRIPT_DIR = Path(__file__).resolve().parent


# ===========================================================================
# CONFIGS
# ===========================================================================

CONFIGS = {
    "niri": SCRIPT_DIR / "niri",
    "noctalia": SCRIPT_DIR / "noctalia",
    "alacritty": SCRIPT_DIR / "alacritty",
    "fastfetch": SCRIPT_DIR / "fastfetch",
}


# ===========================================================================
# PACKAGES
# ===========================================================================

# Основной список пакетов.
#
# code намеренно отсутствует:
# VS Code устанавливается отдельно на шаге 8 именно как
# proprietary Flatpak-версия.

PACKAGES = [
    # GUI
    "clash-verge-rev",
    "docker",
    "droidcam-obs-plugin",
    "flatpak",
    "krita",
    "lact",
    "mpv",
    "mpvpaper",
    "nwg-look",
    "obsidian",
    "obs-studio",
    "opentabletdriver",
    "prismlauncher",
    "protonplus",
    "shelly",
    "steam",
    "telegram-desktop",
    "vesktop-bin",

    # Console
    "tree",
    "ipset",
    "ntfs-3g",
    "yt-dlp",

    # Keyrings / mirrors
    "archlinux-keyring",
    "cachyos-keyring",
    "cachyos-plymouth-bootanimation",
    "cachyos-plymouth-theme",
    "chaotic-keyring",
    "chaotic-mirrorlist",

    # Screenshot / OCR
    "grim",
    "slurp",
    "wf-recorder",
    "xclip",
    "tesseract",
    "tesseract-data-eng",
    "tesseract-data-rus",
    "zbar",
    "ffmpeg",

    # Noctalia screen toolkit
    "imagemagick",
    "curl",
    "jq",
    "bc",
    "xdg-utils",
    "gpu-screen-recorder",
    "satty",

    # Aseprite
    "clang",
    "cmake",
    "ninja",
    "gcc",
    "fontconfig",
    "mesa",
    "libx11",
    "libxcursor",
    "libxi",
    "libxrandr",
    "libwebp",

    # Other
    "uv",

    # Needed by Aseprite build.sh
    "unzip",
]


# Packages that must exist before some early steps.
BOOTSTRAP_PACKAGES = [
    "git",
    "base-devel",
    "curl",
    "wget",
]


# ===========================================================================
# OUTPUT
# ===========================================================================

def log(message: str, level: str = "INFO") -> None:
    prefixes = {
        "INFO": "[INFO]",
        "OK": "[ OK ]",
        "WARN": "[WARN]",
        "ERROR": "[ERROR]",
        "STEP": "\n==========",
    }

    prefix = prefixes.get(level, "[INFO]")
    print(f"{prefix} {message}")


# ===========================================================================
# CONFIRMATION
# ===========================================================================

def confirm(message: str, auto_yes: bool) -> bool:
    if auto_yes:
        print(f"{message} [Y] (-y)")
        return True

    answer = input(f"{message} [y/N]: ").strip().lower()

    return answer in {
        "y",
        "yes",
        "д",
        "да",
    }


# ===========================================================================
# COMMAND EXECUTION
# ===========================================================================

def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    sudo: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:

    final_command = list(command)

    if sudo:
        final_command.insert(0, "sudo")

    log(f"$ {' '.join(final_command)}")

    return subprocess.run(
        final_command,
        cwd=cwd,
        check=check,
    )


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


# ===========================================================================
# STEP 0
# ===========================================================================

def step_0(auto_yes: bool) -> None:
    log("STEP 0: Проверка Python и базовых зависимостей", "STEP")

    if not command_exists("python3"):
        # Теоретически shell-bootstrap уже должен был установить Python.
        # Это дополнительная защита.
        if not confirm(
            "Python не найден. Установить python?",
            auto_yes,
        ):
            raise RuntimeError("Python необходим для работы установщика.")

        run(
            ["pacman", "-Syu", "--needed", "python"],
            sudo=True,
        )

    log("Python доступен.", "OK")

    missing = [
        package
        for package in BOOTSTRAP_PACKAGES
        if not command_exists(package)
    ]

    if missing:
        log(
            "Не найдены базовые зависимости: "
            + ", ".join(missing)
        )

        if confirm(
            "Установить базовые зависимости?",
            auto_yes,
        ):
            run(
                ["pacman", "-Syu", "--needed"] + missing,
                sudo=True,
            )


# ===========================================================================
# STEP 1
# ===========================================================================

def step_1(auto_yes: bool) -> None:
    log("STEP 1: Zapret + tg-ws-proxy-bin", "STEP")

    # -----------------------------------------------------------------------
    # ZAPRET
    # -----------------------------------------------------------------------

    if confirm(
        "Установить zapret-discord-youtube?",
        auto_yes,
    ):
        zapret_dir = SCRIPT_DIR / "zapret-discord-youtube"

        if not zapret_dir.exists():
            run(
                [
                    "git",
                    "clone",
                    "https://github.com/kartavkun/"
                    "zapret-discord-youtube.git",
                    str(zapret_dir),
                ]
            )
        else:
            log("Репозиторий zapret уже существует.", "INFO")

        # setup.sh — актуальный установочный entry point.
        run(
            ["bash", "setup.sh"],
            cwd=zapret_dir,
        )

        log("Zapret установлен.", "OK")

    # -----------------------------------------------------------------------
    # TG WS PROXY
    # -----------------------------------------------------------------------

    if confirm(
        "Установить tg-ws-proxy-bin из AUR без AUR-helper?",
        auto_yes,
    ):
        tg_dir = SCRIPT_DIR / "tg-ws-proxy-bin"

        if not tg_dir.exists():
            run(
                [
                    "git",
                    "clone",
                    "https://aur.archlinux.org/tg-ws-proxy-bin.git",
                    str(tg_dir),
                ]
            )

        run(
            [
                "makepkg",
                "-si",
                "--noconfirm",
            ],
            cwd=tg_dir,
        )

        log("tg-ws-proxy-bin установлен.", "OK")


# ===========================================================================
# CONFIG BACKUP
# ===========================================================================

def backup_existing(path: Path) -> None:
    if not path.exists():
        return

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(
        f"{path.name}.backup-{timestamp}"
    )

    log(f"Создание резервной копии: {backup}")

    shutil.move(
        str(path),
        str(backup),
    )


# ===========================================================================
# COPY CONFIG
# ===========================================================================

def copy_config(name: str) -> None:
    source = CONFIGS[name]
    destination = CONFIG_DIR / name

    if not source.exists():
        raise FileNotFoundError(
            f"Конфигурация не найдена: {source}"
        )

    CONFIG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_existing(destination)

    log(
        f"Копирование {source} -> {destination}"
    )

    shutil.copytree(
        source,
        destination,
    )

    log(
        f"Конфигурация {name} установлена.",
        "OK",
    )


# ===========================================================================
# STEP 2
# ===========================================================================

def step_2(auto_yes: bool) -> None:
    log("STEP 2: Конфигурация Niri", "STEP")

    if confirm(
        "Установить конфигурацию Niri?",
        auto_yes,
    ):
        copy_config("niri")


# ===========================================================================
# STEP 3
# ===========================================================================

def step_3(auto_yes: bool) -> None:
    log("STEP 3: Конфигурация Noctalia", "STEP")

    if confirm(
        "Установить конфигурацию Noctalia?",
        auto_yes,
    ):
        copy_config("noctalia")


# ===========================================================================
# STEP 4
# ===========================================================================

def step_4(auto_yes: bool) -> None:
    log("STEP 4: Конфигурация Alacritty", "STEP")

    if confirm(
        "Установить конфигурацию Alacritty?",
        auto_yes,
    ):
        copy_config("alacritty")


# ===========================================================================
# STEP 5
# ===========================================================================

def step_5(auto_yes: bool) -> None:
    log("STEP 5: Fastfetch", "STEP")

    if not confirm(
        "Сгенерировать стандартный конфиг Fastfetch и заменить его своим?",
        auto_yes,
    ):
        return

    if not command_exists("fastfetch"):
        log(
            "Fastfetch ещё не установлен."
        )

        if not confirm(
            "Установить fastfetch сейчас?",
            auto_yes,
        ):
            raise RuntimeError(
                "Fastfetch необходим для шага 5."
            )

        run(
            [
                "pacman",
                "-Syu",
                "--needed",
                "fastfetch",
            ],
            sudo=True,
        )

    # Создаём стандартный конфиг.
    run(
        ["fastfetch", "--gen-config"]
    )

    # Теперь заменяем его нашим.
    copy_config("fastfetch")


# ===========================================================================
# STEP 6 — CHAOTIC AUR
# ===========================================================================

def chaotic_enabled() -> bool:
    pacman_conf = Path("/etc/pacman.conf")

    if not pacman_conf.exists():
        return False

    content = pacman_conf.read_text()

    return "[chaotic-aur]" in content


def step_6(auto_yes: bool) -> None:
    log("STEP 6: Подключение Chaotic-AUR", "STEP")

    if not confirm(
        "Подключить Chaotic-AUR?",
        auto_yes,
    ):
        return

    if chaotic_enabled():
        log(
            "Chaotic-AUR уже подключён.",
            "OK",
        )
        return

    # -----------------------------------------------------------------------
    # Official Chaotic-AUR bootstrap
    # -----------------------------------------------------------------------

    run(
        [
            "pacman-key",
            "--recv-key",
            "3056513887B78AEB",
            "--keyserver",
            "keyserver.ubuntu.com",
        ],
        sudo=True,
    )

    run(
        [
            "pacman-key",
            "--lsign-key",
            "3056513887B78AEB",
        ],
        sudo=True,
    )

    run(
        [
            "pacman",
            "-U",
            "--noconfirm",
            "https://cdn-mirror.chaotic.cx/"
            "chaotic-aur/chaotic-keyring.pkg.tar.zst",
            "https://cdn-mirror.chaotic.cx/"
            "chaotic-aur/chaotic-mirrorlist.pkg.tar.zst",
        ],
        sudo=True,
    )

    # Добавляем репозиторий в конец pacman.conf.
    #
    # Это намеренно делает Chaotic-AUR ниже официальных репозиториев
    # CachyOS в конфигурации pacman.

    chaotic_block = (
        "\n# ChashniyDotsCachyOS - Chaotic-AUR\n"
        "[chaotic-aur]\n"
        "Include = /etc/pacman.d/chaotic-mirrorlist\n"
    )

    command = [
        "sh",
        "-c",
        "printf '%s' \"$1\" >> /etc/pacman.conf",
        "sh",
        chaotic_block,
    ]

    run(
        command,
        sudo=True,
    )

    # После добавления нового репозитория обновляем систему полностью.
    run(
        ["pacman", "-Syu"],
        sudo=True,
    )

    log(
        "Chaotic-AUR подключён.",
        "OK",
    )


# ===========================================================================
# STEP 7
# ===========================================================================

def package_exists_in_sync_db(package: str) -> bool:
    result = subprocess.run(
        [
            "pacman",
            "-Si",
            package,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 0


def step_7(auto_yes: bool) -> None:
    log("STEP 7: Установка пакетов", "STEP")

    if not confirm(
        f"Установить пакетный набор ({len(PACKAGES)} пакетов)?",
        auto_yes,
    ):
        return

    # Сначала полный system upgrade.
    #
    # Не используем pacman -Sy.
    run(
        ["pacman", "-Syu"],
        sudo=True,
    )

    # Проверяем наличие каждого пакета.
    missing = [
        package
        for package in PACKAGES
        if not package_exists_in_sync_db(package)
    ]

    if missing:
        print()
        log(
            "Следующие пакеты НЕ найдены в подключённых "
            "pacman-репозиториях:",
            "ERROR",
        )

        for package in missing:
            print(f"    - {package}")

        print()

        raise RuntimeError(
            "Пакетная установка остановлена. "
            "Сначала нужно разобраться с отсутствующими пакетами."
        )

    # Всё существует — устанавливаем одним transaction.
    run(
        [
            "pacman",
            "-S",
            "--needed",
        ] + PACKAGES,
        sudo=True,
    )

    log(
        "Пакеты успешно установлены.",
        "OK",
    )


# ===========================================================================
# STEP 8 — VS CODE
# ===========================================================================

def step_8(auto_yes: bool) -> None:
    log(
        "STEP 8: VS Code из Flatpak",
        "STEP",
    )

    if not confirm(
        "Установить proprietary Visual Studio Code из Flatpak?",
        auto_yes,
    ):
        return

    if not command_exists("flatpak"):
        run(
            [
                "pacman",
                "-Syu",
                "--needed",
                "flatpak",
            ],
            sudo=True,
        )

    run(
        [
            "flatpak",
            "remote-add",
            "--if-not-exists",
            "flathub",
            "https://dl.flathub.org/repo/"
            "flathub.flatpakrepo",
        ]
    )

    run(
        [
            "flatpak",
            "install",
            "-y",
            "flathub",
            "com.visualstudio.code",
        ]
    )

    log(
        "Visual Studio Code установлен.",
        "OK",
    )


# ===========================================================================
# STEP 9 — WHITESUR + ASEPRITE
# ===========================================================================

def step_9(auto_yes: bool) -> None:
    log(
        "STEP 9: WhiteSur + Aseprite",
        "STEP",
    )

    # -----------------------------------------------------------------------
    # WHITESUR
    # -----------------------------------------------------------------------

    if confirm(
        "Установить WhiteSur Icon Theme?",
        auto_yes,
    ):
        whitesur = SCRIPT_DIR / "WhiteSur-icon-theme"

        if whitesur.exists():
            shutil.rmtree(whitesur)

        run(
            [
                "git",
                "clone",
                "https://github.com/vinceliuice/"
                "WhiteSur-icon-theme.git",
                str(whitesur),
            ]
        )

        run(
            [
                "./install.sh",
            ],
            cwd=whitesur,
        )

        log(
            "WhiteSur установлен.",
            "OK",
        )

    # -----------------------------------------------------------------------
    # ASEPRITE
    # -----------------------------------------------------------------------

    if confirm(
        "Скачать и собрать Aseprite?",
        auto_yes,
    ):
        aseprite = SCRIPT_DIR / "aseprite"

        if aseprite.exists():
            shutil.rmtree(aseprite)

        run(
            [
                "git",
                "clone",
                "--recursive",
                "https://github.com/aseprite/aseprite.git",
                str(aseprite),
            ]
        )

        # Современный официальный build.sh:
        #
        # --auto:
        #   автоматическая сборка
        #
        # --norun:
        #   не запускать Aseprite после сборки
        #
        # Скрипт также автоматически работает с нужной Skia.
        run(
            [
                "./build.sh",
                "--auto",
                "--norun",
            ],
            cwd=aseprite,
        )

        log(
            "Aseprite собран.",
            "OK",
        )

        # -------------------------------------------------------------------
        # Установка собранного Aseprite в постоянное место.
        #
        # После этого исходный репозиторий можно удалить.
        # -------------------------------------------------------------------

        install_dir = HOME / ".local" / "opt" / "aseprite"

        if install_dir.exists():
            shutil.rmtree(install_dir)

        install_dir.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        run(
            [
                "cmake",
                "--install",
                "build",
                "--prefix",
                str(install_dir),
            ],
            cwd=aseprite,
        )

        log(
            f"Aseprite установлен в {install_dir}",
            "OK",
        )


# ===========================================================================
# STEP 10 — ASEPRITE LINKS
# ===========================================================================

def step_10(auto_yes: bool) -> None:
    log(
        "STEP 10: Симлинк и .desktop для Aseprite",
        "STEP",
    )

    install_dir = (
        HOME
        / ".local"
        / "opt"
        / "aseprite"
    )

    aseprite_bin = (
        install_dir
        / "bin"
        / "aseprite"
    )

    if not aseprite_bin.exists():
        raise FileNotFoundError(
            f"Aseprite не найден: {aseprite_bin}"
        )

    if not confirm(
        "Создать команду aseprite и .desktop файл?",
        auto_yes,
    ):
        return

    local_bin = HOME / ".local" / "bin"
    local_bin.mkdir(
        parents=True,
        exist_ok=True,
    )

    link = local_bin / "aseprite"

    if link.exists() or link.is_symlink():
        link.unlink()

    link.symlink_to(
        aseprite_bin
    )

    applications = (
        HOME
        / ".local"
        / "share"
        / "applications"
    )

    applications.mkdir(
        parents=True,
        exist_ok=True,
    )

    desktop = applications / "aseprite.desktop"

    desktop.write_text(
        f"""[Desktop Entry]
Type=Application
Name=Aseprite
Comment=Animated sprite editor
Exec={link} %F
Icon=aseprite
Terminal=false
Categories=Graphics;2DGraphics;RasterGraphics;
MimeType=image/png;image/jpeg;image/gif;image/bmp;
"""
    )

    log(
        f"Создан симлинк: {link}",
        "OK",
    )

    log(
        f"Создан desktop-файл: {desktop}",
        "OK",
    )


# ===========================================================================
# STEP 11 — CLEANUP
# ===========================================================================

def step_11(auto_yes: bool) -> None:
    log(
        "STEP 11: Очистка временных репозиториев",
        "STEP",
    )

    if not confirm(
        "Удалить временные репозитории?",
        auto_yes,
    ):
        return

    # ВАЖНО:
    # Никогда больше не удаляем все директории из SCRIPT_DIR.
    #
    # Удаляем только те каталоги, которые наш установщик сам создаёт
    # как временные.

    temporary_repositories = [
        "tg-ws-proxy-bin",
        "WhiteSur-icon-theme",
        "aseprite",
    ]

    for name in temporary_repositories:
        path = SCRIPT_DIR / name

        if not path.exists():
            continue

        log(f"Удаление: {path}")

        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    # Эти каталоги намеренно НЕ удаляются:
    #
    # niri
    # noctalia
    # alacritty
    # fastfetch
    # zapret-discord-youtube
    #
    # Они являются частью самого репозитория пользователя.

    log(
        "Очистка завершена.",
        "OK",
    )


# ===========================================================================
# STEP 12 — RTC
# ===========================================================================

def step_12(auto_yes: bool) -> None:
    log(
        "STEP 12: Local RTC",
        "STEP",
    )

    if not confirm(
        "Перевести системные часы на local RTC?",
        auto_yes,
    ):
        return

    run(
        [
            "timedatectl",
            "set-local-rtc",
            "1",
            "--adjust-system-clock",
        ],
        sudo=True,
    )

    log(
        "RTC переведён в local mode.",
        "OK",
    )


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Установщик ChashniyDotsCachyOS "
            "(CachyOS + Niri + Noctalia)"
        )
    )

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="автоматически подтвердить все шаги",
    )

    args = parser.parse_args()

    print()
    print("=" * 70)
    print(" ChashniyDotsCachyOS")
    print(" CachyOS + Niri + Noctalia installer")
    print("=" * 70)
    print()

    if args.yes:
        log(
            "Режим -y: подтверждения шагов отключены.",
            "WARN",
        )

    steps = [
        ("0", step_0),
        ("1", step_1),
        ("2", step_2),
        ("3", step_3),
        ("4", step_4),
        ("5", step_5),
        ("6", step_6),
        ("7", step_7),
        ("8", step_8),
        ("9", step_9),
        ("10", step_10),
        ("11", step_11),
        ("12", step_12),
    ]

    for number, function in steps:
        try:
            function(args.yes)

        except subprocess.CalledProcessError as error:
            log(
                f"Шаг {number} завершился ошибкой. "
                f"Код возврата: {error.returncode}",
                "ERROR",
            )

            # В -y не продолжаем молча после системной ошибки.
            if args.yes:
                return 1

            if not confirm(
                f"Продолжить после ошибки шага {number}?",
                False,
            ):
                return 1

        except Exception as error:
            log(
                f"Шаг {number} завершился ошибкой: {error}",
                "ERROR",
            )

            if args.yes:
                return 1

            if not confirm(
                f"Продолжить после ошибки шага {number}?",
                False,
            ):
                return 1

    print()
    print("=" * 70)
    log(
        "Установка завершена.",
        "OK",
    )
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())