# app/services/varga_service.py
from dataclasses import dataclass

@dataclass
class DivisionalPosition:
    sign: str       # e.g. 'Aries'
    sign_index: int # 1..12
    degree_in_sign: float


SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def compute_d1(lon: float) -> DivisionalPosition:
    """Rāśi chart: 12 signs of 30° each."""
    norm = lon % 360.0
    sign_index = int(norm // 30)  # 0..11
    deg_in_sign = norm - sign_index * 30.0
    return DivisionalPosition(
        sign=SIGNS[sign_index],
        sign_index=sign_index + 1,
        degree_in_sign=deg_in_sign,
    )


def compute_d9(lon: float) -> DivisionalPosition:
    """
    Navamsa (D9) using standard rule:
      - Movable signs (Aries, Cancer, Libra, Capricorn): start from same sign
      - Fixed signs (Taurus, Leo, Scorpio, Aquarius): start from 9th sign
      - Dual signs (Gemini, Virgo, Sagittarius, Pisces): start from 5th sign
    Each sign is split into 9 parts of 3°20' (3.333...°)
    """
    norm = lon % 360.0
    rasi_index = int(norm // 30)          # 0..11
    deg_in_rasi = norm - rasi_index * 30  # 0..30
    pada_index = int(deg_in_rasi // (30.0 / 9.0))  # 0..8

    movable = {0, 3, 6, 9}
    fixed = {1, 4, 7, 10}
    dual = {2, 5, 8, 11}

    if rasi_index in movable:
        start = rasi_index
    elif rasi_index in fixed:
        start = (rasi_index + 8) % 12  # 9th sign
    else:  # dual
        start = (rasi_index + 4) % 12  # 5th sign

    navamsa_sign_index = (start + pada_index) % 12
    deg_in_navamsa = (deg_in_rasi - pada_index * (30.0 / 9.0)) * 9.0 / 30.0 * 30.0

    return DivisionalPosition(
        sign=SIGNS[navamsa_sign_index],
        sign_index=navamsa_sign_index + 1,
        degree_in_sign=deg_in_navamsa,
    )
