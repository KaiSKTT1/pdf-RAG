from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_community.vectorstores import FAISS

from config import CHUNK_OVERLAP_OPTIONS, CHUNK_SIZE_OPTIONS
from loaders.docx_loader import DOCXLoader
from loaders.pdf_loader import PDFLoader
from rag.embeddings import Embeddings


def _normalize_text(text: str) -> str:
    return " ".join((text or "").lower().split())


def _build_query_from_chunk(text: str) -> str:
    words = (text or "").split()
    if not words:
        return ""

    if len(words) > 24:
        return " ".join(words[8:24])
    return " ".join(words[: min(16, len(words))])


def _sample_indices(total: int, max_samples: int = 20) -> list[int]:
    if total <= max_samples:
        return list(range(total))

    step = max(1, total // max_samples)
    indices = list(range(0, total, step))
    return indices[:max_samples]


def _load_chunks_for_config(data_dir: Path, chunk_size: int, chunk_overlap: int):
    pdf_loader = PDFLoader()
    docx_loader = DOCXLoader()
    chunks = []

    for file_path in sorted(data_dir.iterdir()):
        if file_path.suffix.lower() == ".pdf":
            chunks.extend(
                pdf_loader.load_and_split(
                    str(file_path),
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            )
        elif file_path.suffix.lower() == ".docx":
            chunks.extend(
                docx_loader.load_and_split(
                    str(file_path),
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            )

    return chunks


def evaluate_chunk_configs(data_dir: Path):
    embedder = Embeddings().embedder
    results = []

    for chunk_size in CHUNK_SIZE_OPTIONS:
        for chunk_overlap in CHUNK_OVERLAP_OPTIONS:
            if chunk_overlap >= chunk_size:
                continue

            chunks = _load_chunks_for_config(data_dir, chunk_size, chunk_overlap)
            if not chunks:
                results.append(
                    {
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                        "num_chunks": 0,
                        "num_queries": 0,
                        "top1_accuracy": 0.0,
                        "top5_accuracy": 0.0,
                    }
                )
                continue

            vectorstore = FAISS.from_documents(chunks, embedder)
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5},
            )

            query_indices = _sample_indices(len(chunks), max_samples=20)
            top1_hits = 0
            top5_hits = 0
            valid_queries = 0

            for idx in query_indices:
                source_chunk = chunks[idx]
                source_text = _normalize_text(source_chunk.page_content)
                query = _build_query_from_chunk(source_chunk.page_content)

                if not source_text or not query:
                    continue

                valid_queries += 1
                retrieved_docs = retriever.invoke(query)
                retrieved_texts = [_normalize_text(doc.page_content) for doc in retrieved_docs]

                if retrieved_texts and retrieved_texts[0] == source_text:
                    top1_hits += 1
                if source_text in retrieved_texts:
                    top5_hits += 1

            if valid_queries == 0:
                top1_accuracy = 0.0
                top5_accuracy = 0.0
            else:
                top1_accuracy = top1_hits / valid_queries
                top5_accuracy = top5_hits / valid_queries

            results.append(
                {
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "num_chunks": len(chunks),
                    "num_queries": valid_queries,
                    "top1_accuracy": top1_accuracy,
                    "top5_accuracy": top5_accuracy,
                }
            )

    results.sort(
        key=lambda item: (
            item["top1_accuracy"],
            item["top5_accuracy"],
            -item["num_chunks"],
        ),
        reverse=True,
    )
    return results


def main():
    data_dir = PROJECT_ROOT / "data"

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    results = evaluate_chunk_configs(data_dir)

    print("chunk_size,chunk_overlap,num_chunks,num_queries,top1_accuracy,top5_accuracy")
    for item in results:
        print(
            f"{item['chunk_size']},{item['chunk_overlap']},{item['num_chunks']},"
            f"{item['num_queries']},{item['top1_accuracy']:.4f},{item['top5_accuracy']:.4f}"
        )


if __name__ == "__main__":
    main()
