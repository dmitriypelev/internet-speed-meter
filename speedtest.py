#!/usr/bin/env python3
"""Measure download speed using ten sequential HTTP requests."""

import argparse
import sys
from http.client import HTTPException
from time import perf_counter
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024


def download(url):
    request = Request(url, headers={
        "User-Agent": "internet-speed-meter/1.0",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
    })
    size = 0
    started = perf_counter()
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise ValueError(f"ожидался HTTP 200, получен {response.status}")
        while chunk := response.read(CHUNK_SIZE):
            size += len(chunk)
        expected = response.headers.get("Content-Length")
        if expected is not None and size != int(expected):
            raise ValueError("соединение закрыто до завершения скачивания")
    elapsed = perf_counter() - started
    if size == 0:
        raise ValueError("сервер вернул пустой ответ")
    return size, elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Замер скорости: 10 последовательных скачиваний файла."
    )
    parser.add_argument("url", help="HTTP(S)-адрес большого файла или картинки")
    args = parser.parse_args()
    try:
        address = urlsplit(args.url)
        if address.scheme not in ("http", "https") or not address.hostname:
            raise ValueError("нужен корректный HTTP(S)-адрес")
    except ValueError as error:
        parser.error(str(error))

    total_bytes = 0
    total_time = 0.0
    successful = 0
    for number in range(1, REQUEST_COUNT + 1):
        try:
            size, elapsed = download(args.url)
        except (URLError, OSError, HTTPException, ValueError) as error:
            print(f"[{number}/{REQUEST_COUNT}] Ошибка: {error}", file=sys.stderr)
            continue
        total_bytes += size
        total_time += elapsed
        successful += 1
        print(f"[{number}/{REQUEST_COUNT}] {size:,} байт за {elapsed:.3f} с", flush=True)

    print(f"\nУспешных запросов: {successful}/{REQUEST_COUNT}")
    if not successful:
        print("Не удалось измерить скорость.", file=sys.stderr)
        return 1
    megabytes_per_second = total_bytes / total_time / 1_000_000
    print(f"Среднее время запроса: {total_time / successful:.3f} с")
    print(f"Скачано: {total_bytes:,} байт ({total_bytes / 1_000_000:.3f} МБ)")
    print(f"Скорость: {megabytes_per_second * 8:.2f} Мбит/с "
          f"({megabytes_per_second:.2f} МБ/с)")
    return 0 if successful == REQUEST_COUNT else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nЗамер прерван.", file=sys.stderr)
        sys.exit(130)
