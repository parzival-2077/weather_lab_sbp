from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def export_to_markdown(city: str, rows: list, output_file: str | None = None) -> str:
    if not rows:
        raise ValueError("Нет данных для экспорта в Markdown.")

    output_file = output_file or os.getenv("OUTPUT_FILE", "weather_report.md")
    dates = [r.forecast_date for r in rows]
    period = f"{min(dates)} — {max(dates)}"

    lines = [
        "# Прогноз погоды",
        "",
        f"Локация: **{city}**",
        "",
        f"Период: {period}",
        "",
        "| Дата | Мин. темп. (°C) | Макс. темп. (°C) | Описание | Влажность (%) | Ветер (м/с) |",
        "|------|-----------------|------------------|----------|---------------|-------------|",
    ]

    for r in rows:
        lines.append(
            f"| {r.forecast_date} | {r.temp_min:+.1f} | {r.temp_max:+.1f} | "
            f"{r.description} | {r.humidity} | {r.wind_speed:.1f} |"
        )

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as e:
        raise RuntimeError(f"Не удалось записать файл {output_file}: {e}") from e

    logger.info("Markdown сохранён: %s", output_file)
    return output_file