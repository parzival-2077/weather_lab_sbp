from __future__ import annotations

from datetime import datetime, date, timezone
from sqlalchemy import create_engine, Integer, String, Float, Date, DateTime, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
import logging
import os

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class WeatherForecast(Base):
    __tablename__ = "weather_forecast"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    temp_min: Mapped[float] = mapped_column(Float, nullable=False)
    temp_max: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[int] = mapped_column(Integer, nullable=False)
    wind_speed: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<WeatherForecast {self.city} {self.forecast_date}>"


def get_engine():
    db_url = os.getenv("DB_URL", "sqlite:///weather_lab.db")
    return create_engine(db_url, echo=False, future=True)


def init_db(engine) -> None:
    Base.metadata.create_all(engine)
    logger.info("Таблицы созданы/проверены.")


def save_forecast(engine, city: str, daily: list[dict]) -> int:
    saved = 0
    with Session(engine) as session:
        for row in daily:
            exists = session.execute(
                select(WeatherForecast).where(
                    WeatherForecast.city == city,
                    WeatherForecast.forecast_date == _to_date(row["date"]),
                )
            ).scalar_one_or_none()
            if exists:
                logger.info("Пропуск дубликата: %s %s", city, row["date"])
                continue

            session.add(WeatherForecast(
                city=city,
                forecast_date=_to_date(row["date"]),
                temp_min=row["temp_min"],
                temp_max=row["temp_max"],
                humidity=int(round(row["humidity_avg"])),
                wind_speed=row["wind_max"],
                description=row["description"],
            ))
            saved += 1

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Ошибка записи в БД: %s", e)
            raise RuntimeError("Не удалось сохранить данные в БД.") from e

    logger.info("Сохранено записей: %d", saved)
    return saved


def load_forecast(engine, city: str) -> list[WeatherForecast]:
    with Session(engine) as session:
        rows = session.execute(
            select(WeatherForecast)
            .where(WeatherForecast.city == city)
            .order_by(WeatherForecast.forecast_date)
        ).scalars().all()
        return list(rows)


def _to_date(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()
