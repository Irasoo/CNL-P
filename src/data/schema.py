from typing import Literal, List, Optional, Dict, get_origin, get_args, NotRequired
from typing_extensions import TypedDict

class ATopping(TypedDict):
    _type: Literal["Boba", "Pudding", "TaroPaste"]
    quantity: int


class BTopping(TypedDict):
    _type: Literal["Boba", "Pudding", "CoconutJelly"]
    quantity: int


class ABrandTea(TypedDict):
    product: Literal["MilkTea", "FruitTea", "PureTea"]
    toppings: List[ATopping]
    size: Literal["L", "M", "S"]


class BBrandTea(TypedDict):
    product: Literal["MilkTea", "FruitTea", "PureTea"]
    toppings: List[BTopping]
    size: Literal["L", "M", "S"]


class RapidAPIHeaders(TypedDict):
    key: str
    movie_host: str
    game_host: str
    weather_host: str
    sport_host: str
    finance_host: str
    news_host: str


class PositionInfo(TypedDict):
    longitude_and_latitude: str
    region: Literal['UK', 'US', 'RU', 'IN', 'BR', 'DE', 'FR', 'CA']


class UserInfo(TypedDict):
    id: int
    language: str
    password: str
    position: PositionInfo
    key_and_host: RapidAPIHeaders


class FitnessAPIHeaders(TypedDict):
    key: str
    fitness_host: str
    diet_host: str





WorkoutType = Literal["strength", "cardio", "flexibility", "balance"]


class WorkoutPlan(TypedDict):
    exercises: List[str]
    duration_in_minutes: int
    intensity: str


RequestType = Literal['game', 'finance', 'sport', 'movie', 'weather', 'Google News']

