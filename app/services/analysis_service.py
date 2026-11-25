from app.config import Settings
from app.schemas import LinkResponse
from app.services.llm_service import ModelError, generate_report
from app.services.website_extractor import extract_website


async def analyze(url: str, settings: Settings) -> LinkResponse:
    website, pages = await extract_website(url)
    report = await generate_report(pages, settings)
    queries = report.analysis.target_search_queries
    if (len({query.query.casefold() for query in queries}) != 5
            or len({platform for query in queries for platform in query.platforms}) != 5):
        raise ModelError("The provider did not return five distinct queries covering all platforms.")
    evidence = [" ".join(source.casefold().split())
                for page in pages for source in [page["text"], *page["headings"]]]
    for service in report.analysis.top_services:
        quote = " ".join((service.evidence or "").casefold().split())
        if service.status == "observed" and (not quote or not any(quote in source for source in evidence)):
            service.status = "inferred"
        if service.status == "inferred":
            service.evidence = None
    return LinkResponse(website=website, **report.model_dump())
