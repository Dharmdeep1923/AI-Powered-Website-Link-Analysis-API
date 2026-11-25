import secrets
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import Settings
from app.schemas import LinkRequest, LinkResponse
from app.services.analysis_service import analyze
from app.services.llm_service import ModelError, ModelRateLimited, ModelUnavailable
from app.utils.validators import WebsiteError

app = FastAPI(title="Website Link Analysis", version="1.0.0")
settings = Settings()
key_header = APIKeyHeader(name="X-Analysis-Key", auto_error=False)


@app.post("/link-analysis", response_model=LinkResponse)
async def link_analysis(
    request: LinkRequest,
    key: Annotated[str | None, Security(key_header)],
) -> LinkResponse:
    expected = settings.analysis_api_key
    if expected and not secrets.compare_digest(
        (key or "").encode(), expected.get_secret_value().encode()
    ):
        raise HTTPException(401, "A valid analysis key is required.")
    if request.url.username is not None:
        raise HTTPException(422, "Website credentials are not accepted.")
    if not settings.gemini_api_key or not settings.gemini_api_key.get_secret_value():
        raise HTTPException(503, "The analysis provider has not been configured.")
    try:
        return await analyze(str(request.url), settings)
    except WebsiteError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (httpx.TimeoutException, TimeoutError) as exc:
        raise HTTPException(504, "The website took too long to respond.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(502, "The website could not be fetched.") from exc
    except ModelUnavailable as exc:
        raise HTTPException(503, str(exc), headers={"Retry-After": "5"}) from exc
    except ModelRateLimited as exc:
        raise HTTPException(429, str(exc)) from exc
    except ModelError as exc:
        raise HTTPException(502, str(exc)) from exc
