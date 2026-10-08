import asyncio

from backend.services.embedder import FastEmbedder as SentenceTransformer  # ONNX replacement, same .encode() API

from backend.core.config import SENTENCE_TRANSFORMER_MODEL
from backend.services.jobs.ingestion import sync_enabled_sources


async def main():

    print("Loading embedding model...")

    embedder = SentenceTransformer(
        SENTENCE_TRANSFORMER_MODEL
    )

    print("Embedding model loaded.")

    print("\nStarting job source sync...\n")

    results = await sync_enabled_sources(
        embedder=embedder,
    )

    print("\nJob sync results:")

    for result in results:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())