import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="API Gateway")

SERVICES = {
    "benefits": "http://127.0.0.1:8001",
    "backend": "http://127.0.0.1:8000",
}

@app.api_route("/gateway/benefits/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_benefits(path: str, request: Request):
    url = f"{SERVICES['benefits']}/benefits/{path}"
    body = await request.body()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                request.method, url,
                content=body,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                params=request.query_params,
                timeout=5,
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Servicio de beneficios no disponible")

    return JSONResponse(content=response.json(), status_code=response.status_code)