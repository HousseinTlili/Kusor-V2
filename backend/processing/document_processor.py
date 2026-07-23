import fitz  # PyMuPDF
import re
from pathlib import Path
import ollama
import chromadb


class DocumentProcessor:
    """
    Module 3 — Pipeline de prétraitement documentaire.
    Étape 1 : extraction de texte (PyMuPDF, fallback OCR si nécessaire).
    """

    def __init__(self, ocr_lang="fra"):
        self.ocr_lang = ocr_lang

    def extract_text(self, pdf_path: str) -> list[dict]:
        """Retourne une liste de dicts: [{"page": int, "text": str}, ...]"""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {pdf_path}")

        doc = fitz.open(pdf_path)
        pages_content = []

        for i, page in enumerate(doc):
            text = page.get_text().strip()
            if len(text) < 20:
                text = self._ocr_fallback(page)
            pages_content.append({"page": i + 1, "text": text})

        doc.close()
        return pages_content

    def _ocr_fallback(self, page) -> str:
        """OCR via Tesseract pour les pages scannées (image uniquement)."""
        import pytesseract
        from PIL import Image
        import io

        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img, lang=self.ocr_lang)
    def chunk_text(self, pages_content: list[dict], min_tokens: int = 100, max_tokens: int = 800) -> list[dict]:
        """
        Découpe le texte en chunks par paragraphes, en respectant une taille
        min/max approximative (en mots, comme proxy simple pour les tokens).
        """
        chunks = []
        chunk_id = 0

        for page_data in pages_content:
            page_num = page_data["page"]
            text = page_data["text"]

            paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\.\s+(?=[A-ZÀ-Ü])", text) if p.strip()]

            current_chunk = ""
            for para in paragraphs:
                word_count = len(current_chunk.split()) + len(para.split())

                if word_count > max_tokens and current_chunk:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "page": page_num,
                        "text": current_chunk.strip(),
                    })
                    chunk_id += 1
                    current_chunk = para
                else:
                    current_chunk += " " + para

            if current_chunk.strip() and len(current_chunk.split()) >= min_tokens // 2:
                chunks.append({
                    "chunk_id": chunk_id,
                    "page": page_num,
                    "text": current_chunk.strip(),
                })
                chunk_id += 1

        return chunks
    def embed_and_store(self, chunks: list[dict], document_id: str, chroma_host: str = "localhost", chroma_port: int = 8001):
        """
        Génère les embeddings de chaque chunk via Ollama (nomic-embed-text)
        et les stocke dans ChromaDB avec leurs métadonnées.
        """
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collection = client.get_or_create_collection(name="circulars")

        ids, embeddings, documents, metadatas = [], [], [], []

        for chunk in chunks:
            response = ollama.embeddings(model="nomic-embed-text", prompt=chunk["text"])
            embedding = response["embedding"]

            ids.append(f"{document_id}_chunk_{chunk['chunk_id']}")
            embeddings.append(embedding)
            documents.append(chunk["text"])
            metadatas.append({
                "document_id": document_id,
                "chunk_index": chunk["chunk_id"],
                "page_number": chunk["page"],
            })

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return len(ids)

    def extract_circular_references(self, text: str) -> list[str]:
        """Détecte les références explicites à d'autres circulaires."""
        pattern = r"circulaire[s]?\s*(?:aux\s+\w+\s+)?n[°o]?\s*(\d{4}-\d{2})"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        return list(set(matches))

if __name__ == "__main__":
    processor = DocumentProcessor()
    pdf_path = "/home/nour/kusor/data/circulars/Cir_2022_01_fr.pdf"

    pages = processor.extract_text(pdf_path)
    print(f"✅ {len(pages)} pages extraites\n")

    all_text = " ".join(p["text"] for p in pages)
    refs = processor.extract_circular_references(all_text)
    print(f"📎 Références de circulaires détectées : {refs}\n")

    chunks = processor.chunk_text(pages)
    print(f"🧩 {len(chunks)} chunks créés\n")

    count = processor.embed_and_store(chunks, document_id="circulaire_2022_01")
    print(f"💾 {count} chunks embeddés et stockés dans ChromaDB")