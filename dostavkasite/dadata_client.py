"""
Клиент DaData для геокодирования и подсказок адресов.
"""
from django.conf import settings
from django.core.cache import cache

GEOCODE_CACHE_TIMEOUT = 600  # 10 минут — один и тот же адрес не дергаем API повторно


def get_dadata_client():
    """Создать клиент DaData (lazy, чтобы не падать при старте без ключей)."""
    api_key = getattr(settings, 'DADATA_API_KEY', None)
    secret = getattr(settings, 'DADATA_SECRET_KEY', None)
    if not api_key or not secret or api_key == "your-dadata-api-key":
        return None
    try:
        from dadata import Dadata
        return Dadata(api_key, secret)
    except ImportError:
        return None


def _coords_from_clean_result(result):
    """Из ответа DaData clean извлечь координаты и поля адреса."""
    if not result or not result.get('geo_lat') or not result.get('geo_lon'):
        return None
    try:
        lat = float(result['geo_lat'])
        lng = float(result['geo_lon'])
    except (TypeError, ValueError):
        return None
    return {
        'lat': lat,
        'lng': lng,
        'city': result.get('city') or result.get('settlement') or result.get('region', ''),
        'street': result.get('street', ''),
        'house': result.get('house', ''),
        'block': result.get('block') or None,
        'region': result.get('region', ''),
    }


def _coords_from_suggestion_data(data):
    """geo_lat/geo_lon из объекта data подсказки DaData."""
    if not data:
        return None
    lat, lng = data.get('geo_lat'), data.get('geo_lon')
    if lat is None or lng is None:
        return None
    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        return None
    return {
        'lat': lat,
        'lng': lng,
        'city': data.get('city') or data.get('settlement') or data.get('region_with_type', '') or '',
        'street': data.get('street') or data.get('street_with_type') or '',
        'house': data.get('house') or '',
        'block': data.get('block') or None,
        'region': data.get('region') or '',
    }


def geocode_address(address_str):
    """
    Геокодирование адреса через DaData (получить lat, lng).
    Сначала standardize/clean; если координат нет (часто у деревень/сёл) — fallback через suggest.
    Результат кэшируется на 10 мин.
    Возвращает dict с ключами: lat, lng, city, street, house, block, region
    или None при ошибке.
    """
    if not address_str or not str(address_str).strip():
        return None
    key = "geocode:" + str(address_str).strip()[:250]
    cached = cache.get(key)
    if cached is not None:
        return cached

    client = get_dadata_client()
    if not client:
        return None

    def try_cache_and_return(out):
        cache.set(key, out, GEOCODE_CACHE_TIMEOUT)
        return out

    try:
        result = client.clean(name="address", source=address_str)
        out = _coords_from_clean_result(result)
        if out:
            return try_cache_and_return(out)
    except Exception as e:
        print(f"Ошибка DaData geocode clean: {e}")

    # Fallback: подсказки — для населённых пунктов «село …», деревень clean часто без координат
    try:
        suggestions = client.suggest(name="address", query=address_str.strip(), count=10)
        for s in suggestions or []:
            data = s.get('data') or {}
            out = _coords_from_suggestion_data(data)
            if out:
                return try_cache_and_return(out)
    except Exception as e:
        print(f"Ошибка DaData geocode suggest: {e}")

    return None


def geocode_address_variants(*variants):
    """
    Пробует несколько строк адреса по очереди (например с префиксом «Россия»).
    Возвращает первый успешный результат geocode_address или None.
    """
    seen = set()
    for v in variants:
        if not v:
            continue
        s = str(v).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        res = geocode_address(s)
        if res:
            return res
    return None


def suggest_address(query, count=10):
    """
    Подсказки адресов через DaData Suggest API.
    Возвращает список dict: [{value, unrestricted_value, data: {city, street, house, geo_lat, geo_lon, ...}}, ...]
    """
    client = get_dadata_client()
    if not client:
        return []

    try:
        result = client.suggest(name="address", query=query, count=count)
        return result or []
    except Exception as e:
        print(f"Ошибка DaData suggest: {e}")
        return []


def parse_suggestion_to_address(suggestion):
    """
    Преобразует объект подсказки DaData в плоский словарь для формы.
    data.city, data.street, data.house, data.block, data.flat, data.geo_lat, data.geo_lon
    """
    if not suggestion or 'data' not in suggestion:
        return None
    data = suggestion['data']
    return {
        'city': data.get('city') or data.get('settlement') or data.get('area') or data.get('region', ''),
        'street': data.get('street', ''),
        'house': data.get('house', ''),
        'block': data.get('block') or '',
        'entrance': data.get('entrance') or '',
        'floor': data.get('floor') or '',
        'apartment': data.get('flat') or '',
        'geo_lat': data.get('geo_lat') or '',
        'geo_lon': data.get('geo_lon') or '',
        'value': suggestion.get('value', ''),
        'unrestricted_value': suggestion.get('unrestricted_value', ''),
    }
