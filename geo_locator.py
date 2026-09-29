import logging
import os
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def get_loc(timeout: float = 5.0):
    url = os.getenv("GEO_API_URL", "https://ipinfo.io/json")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
       # print(response
        city = data.get('city')
        loc = data.get("loc")
        return {"city": city, "loc": loc, "raw": data}
    
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError("Ошибка соединения. Проверьте интернет.") from e
    except requests.exceptions.Timeout as e:
        raise TimeoutError(
            f"Сервер не ответил за {timeout} секунд."
        ) from e
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        if code == 429:
            raise RuntimeError("Превышен лимит запросов.") from e
        raise RuntimeError(f"API вернул HTTP {code}.") from e
    except requests.exceptions.JSONDecodeError as e:
        raise ValueError(f"Некорректный ответ от API: {e}") from e
    

