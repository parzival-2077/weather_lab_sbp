from __future__ import annotations

import logging
import sys
from dotenv import load_dotenv

from geo_locator import get_loc
from weather_client import get_weather
from db_models import get_engine, init_db, save_forecast, load_forecast
from exporter import export_to_markdown


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    load_dotenv()

    try:
        info = get_loc()
    except (ConnectionError, TimeoutError, RuntimeError, ValueError) as e:
        logger.error("Не удалось определить местоположение: %s", e)
        return 1

    city = info["city"]
    loc = info["loc"]
    if not city or not loc:
        logger.error("Гео-API вернул неполные данные: %s", info)
        return 1

    print(f"Город: {city}")
    print(f"Координаты: {loc}")
    lat, lon = (float(x) for x in loc.split(","))

    try:
        weather = get_weather(lat, lon)
    except (ConnectionError, TimeoutError, RuntimeError, ValueError) as e:
        logger.error("Ошибка получения прогноза: %s", e)
        return 2

    for d in weather:
        print(
            f"{d['date']}: мин:{d['temp_min']:+.1f} °C, макс:{d['temp_max']:+.1f} °C, "
            f"влажность {d['humidity_avg']}%, ветер до {d['wind_max']} м/с, "
            f"{d['description']}"
        )

    try:
        engine = get_engine()
        init_db(engine)
        saved = save_forecast(engine, city, weather)
    except RuntimeError as e:
        logger.error("Ошибка БД: %s", e)
        return 3
    print(f"Сохранено записей: {saved}")

    try:
        rows = load_forecast(engine, city)
        path = export_to_markdown(city, rows)
    except (RuntimeError, ValueError) as e:
        logger.error("Ошибка экспорта: %s", e)
        return 4
    print(f"Отчёт: {path}")

    print("\nГотово.")
    return 0


if __name__ == "__main__":
    sys.exit(main())