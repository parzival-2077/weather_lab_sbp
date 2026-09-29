from datetime import datetime, timezone
import os
import requests
from collections import Counter
from dotenv import load_dotenv
from statistics import mean
load_dotenv()

url = os.getenv("WEATHER_API_BASE_URL")
api_key = os.getenv("WEATHER_API_KEY")

def get_weather(
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        timeout: float = 10.0):

    if lat is not None and lon is not None:
        params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric",
                "lang": "ru",
            }

    elif city:
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "ru",
        }
    else:
        raise ValueError("Нужно передать либо city, либо lat и lon.")

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        # for i in data['list']:
        #     print( i['dt_txt'], '{0:+3.0f}'.format(i['main']['temp']), i['weather'][0]['description'] )
        buckets: dict[str, list[dict]] = {}
        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            buckets.setdefault(dt.strftime("%Y-%m-%d"), []).append(item)

        result = []
        for day in sorted(buckets)[:4]:
            items = buckets[day]

            noon = next(
                (i for i in items
                if datetime.fromtimestamp(i["dt"], tz=timezone.utc).hour == 12),
                None,
            )
            if noon and noon.get("weather"):
                description = noon["weather"][0]["description"]
            else:
                descs = [i["weather"][0]["description"] for i in items if i.get("weather")]
                description = Counter(descs).most_common(1)[0][0] if descs else "нет данных"

            result.append({
                "date": day,
                "temp_min": min(i["main"]["temp_min"] for i in items),
                "temp_max": max(i["main"]["temp_max"] for i in items),
                "humidity_avg": round(mean(i["main"]["humidity"] for i in items), 1),
                "wind_max": max(i["wind"]["speed"] for i in items),
                "description": description,
            })
        return result

        
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError("Ошибка соединения. Проверьте интернет.") from e
    except requests.exceptions.Timeout as e:
        raise TimeoutError(
            f"Сервер не ответил за {timeout} секунд."
        ) from e
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        if code == 401:
            raise ValueError("Ошибка API-ключа.") from e
        if code == 404:
            raise ValueError("Город не найден.") from e
        if code == 429:
            raise RuntimeError("Превышен лимит запросов.") from e
        raise RuntimeError(f"API вернул HTTP {code}.") from e
    except requests.exceptions.JSONDecodeError as e:
        raise ValueError(f"Некорректный ответ от API: {e}") from e

    
