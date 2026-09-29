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

    info = get_loc()

    city = info["city"]
    loc = info["loc"]

    print(f"Город: {city}")
    print(f"Координаты: {loc}")
    lat, lon = (float(x) for x in loc.split(","))

    weather = get_weather(city, lat, lon)


    for d in weather:
        print(
            f"{d['date']}: мин:{d['temp_min']:+.1f} °C, макс:{d['temp_max']:+.1f} °C, "
            f"влажность {d['humidity_avg']}%, ветер до {d['wind_max']} м/с, "
            f"{d['description']}"
        )

    engine = get_engine()
    init_db(engine)
    saved = save_forecast(engine, city, weather)

    print(f"Сохранено записей: {saved}")

    rows = load_forecast(engine, city)
    path = export_to_markdown(city, rows)
    print(f"Отчёт: {path}")

    print("\nПрограмма завершила свою работу.")
    return 0


if __name__ == "__main__":
    sys.exit(main())