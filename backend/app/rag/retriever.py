from uuid import UUID

from app.database.supabase import get_supabase_admin
from app.rag.embeddings import EmbeddingService


class SupabaseRetriever:
    async def retrieve(self, user_id: UUID, question: str, course_id: UUID | None, top_k: int) -> list[dict]:
        embedding = await EmbeddingService().embed_query(question)
        response = get_supabase_admin().rpc(
            "match_document_chunks",
            {
                "query_embedding": embedding,
                "match_count": top_k,
                "filter_user_id": str(user_id),
                "filter_course_id": str(course_id) if course_id else None,
            },
        ).execute()
        return response.data
