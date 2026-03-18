from __future__ import annotations

from pydantic import BaseModel


class OverviewData(BaseModel):
    total_count: int
    avg_rating: float
    avg_price: float
    district_count: int


class DistrictCount(BaseModel):
    name: str
    count: int


class CuisineCount(BaseModel):
    name: str
    count: int
    percentage: float


class PriceRangeCount(BaseModel):
    label: str
    count: int


class RatingRangeCount(BaseModel):
    range: str
    count: int


class DistrictAvgPrice(BaseModel):
    name: str
    avg_price: float


class KeywordCount(BaseModel):
    word: str
    count: int


class AreaDistributionData(BaseModel):
    districts: list[DistrictCount]


class CuisineDistributionData(BaseModel):
    cuisines: list[CuisineCount]


class PriceDistributionData(BaseModel):
    ranges: list[PriceRangeCount]


class RatingDistributionData(BaseModel):
    ratings: list[RatingRangeCount]


class AreaAvgPriceData(BaseModel):
    districts: list[DistrictAvgPrice]


class ReviewKeywordsData(BaseModel):
    positive: list[KeywordCount]
    negative: list[KeywordCount]
