# ChashniyDotsCachyOS

Установочный скрипт и конфиги для быстрой настройки **CachyOS + Niri + Noctalia**.
Скрипт написан на Python, поддерживает пошаговое выполнение с подтверждением или
полностью автоматический режим.

---

## Что делает скрипт

Скрипт выполняет 12 шагов:

| # | Шаг | Описание |
|---|-----|----------|
| 0 | Проверка Python | Устанавливает `python` из репозиториев CachyOS, если его нет |
| 1 | Zapret + TG WS Proxy | Клонирует и устанавливает `zapret-discord-youtube` и `tg-ws-proxy-bin` (AUR) |
| 2 | Конфиг Niri | Копирует `niri/` в `~/.config/niri` |
| 3 | Конфиг Noctalia | Копирует `noctalia/` в `~/.config/noctalia` |
| 4 | Конфиг Alacritty | Копирует `alacritty/` в `~/.config/alacritty` |
| 5 | Конфиг Fastfetch | Генерирует стандартный конфиг и заменяет своим |
| 6 | ChaoticAUR | Подключает репозиторий с низким приоритетом |
| 7 | Пакеты | Устанавливает GUI-приложения, утилиты, зависимости для сборки |
| 8 | VS Code | Устанавливает проприетарную версию из Flatpak |
| 9 | WhiteSur + Aseprite | Клонирует и собирает тему иконок и редактор |
| 10 | Симлинки Aseprite | Создаёт симлинк и `.desktop` для запуска без локального репо |
| 11 | Очистка | Удаляет временные репозитории (кроме zapret) |
| 12 | RTC | Переводит системное время на локальное RTC (для dual-boot с Windows) |

---

## Требования

- **CachyOS** (или любой Arch-based дистрибутив с `pacman`)
- **`base-devel`** — для сборки AUR-пакетов через `makepkg`
- **`python`** — устанавливается автоматически на шаге 0, если отсутствует
- Интернет-соединение

---

## Установка и запуск

```bash
git clone https://github.com/Chashniy/ChashniyDotsCachyOS.git
cd ChashniyDotsCachyOS
chmod +x install.py
./install.py
