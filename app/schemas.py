from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LinkRequest(Schema):
    url: HttpUrl


class Brand(Schema):
    name: str
    category: str
    summary: str
    products_and_services: list[str]


class Competitor(Schema):
    name: str
    comparison: str
    strengths: list[str]
    gaps: list[str]
    status: Literal["AI-generated suggestion"]


class CompetitorAnalysis(Schema):
    brand_overview: str
    competitors: list[Competitor] = Field(max_length=5)
    strengths: list[str]
    opportunities: list[str]


Platform = Literal["Google Search", "Facebook", "Instagram", "LinkedIn", "X"]


class SearchQuery(Schema):
    query: str
    platforms: list[Platform] = Field(min_length=1)
    intent: str
    business_relevance: str
    target_audience: str


class SEO(Schema):
    primary_keyword: str
    secondary_keywords: list[str]
    long_tail_keywords: list[str]
    business_keywords: list[str]
    recommended_title: str
    title_structure: str
    meta_description: str
    supporting_content: list[str]


class Service(Schema):
    name: str
    description: str
    target_industry: str
    target_customer: str
    main_benefit: str
    status: Literal["observed", "inferred"]
    evidence: str | None


class Audience(Schema):
    primary_audience: list[str]
    secondary_audience: list[str]
    industries: list[str]
    business_types: list[str]
    customer_profiles: list[str]
    geographical_focus: str | None
    customer_needs: list[str]
    interests: list[str]
    marketing_segments: list[str]


class Analysis(Schema):
    competitor_analysis: CompetitorAnalysis
    target_search_queries: list[SearchQuery] = Field(min_length=5, max_length=5)
    seo_improvements: SEO
    top_services: list[Service] = Field(max_length=5)
    target_audience: Audience


class Report(Schema):
    brand: Brand
    analysis: Analysis


class LinkResponse(Report):
    success: Literal[True] = True
    website: HttpUrl
