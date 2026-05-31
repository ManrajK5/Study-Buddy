from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


class EmbeddingService:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for index in range(0, len(texts), settings.embedding_batch_size):
            batch = texts[index : index + settings.embedding_batch_size]
            if len(batch) == 1:
                embeddings.append(await self.embed_query(batch[0]))
                continue

            payload = await self._invoke_embed_function({"inputs": batch})
            batch_embeddings = payload.get("embeddings")
            if not isinstance(batch_embeddings, list):
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Embedding function returned no embeddings.")
            embeddings.extend(batch_embeddings)
        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        payload = await self._invoke_embed_function({"input": text})
        embedding = payload.get("embedding")
        if not isinstance(embedding, list):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Embedding function returned no embedding.")
        return embedding

    async def _invoke_embed_function(self, body: dict[str, Any]) -> dict[str, Any]:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase URL and anon key are required for the embedding Edge Function.",
            )

        url = f"{settings.supabase_functions_url}/{settings.supabase_embedding_function}"
        headers = {
            "apikey": settings.supabase_anon_key,
            "Authorization": f"Bearer {settings.supabase_anon_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=body, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "Embedding Edge Function failed.", "status_code": response.status_code, "body": response.text},
            )
        return response.json()
