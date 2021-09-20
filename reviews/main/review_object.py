import pydantic
from typing import Optional
import datetime


class Review(pydantic.BaseModel):
    id: str
    user_id: str
    user_name: str
    review_rating: float
    review_text: str
    date: datetime.datetime
    user_picture: Optional[str]
    user_level: Optional[str]
    user_city: Optional[str]
    user_state: Optional[str]
    user_zip: Optional[int]
    reviews_total: Optional[int]
    review_headline: Optional[str]
    review_business_response_date: Optional[datetime.datetime]
    review_business_response_text: Optional[str]
    dump: Optional[str]
