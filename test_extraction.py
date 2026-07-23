import fitz  # PyMuPDF

pdf_path = "/home/nour/kusor/data/circulars/Cir_2022_01_fr.pdf"

doc = fitz.open(pdf_path)
print(f"Nombre de pages : {len(doc)}")
print("-" * 50)

for i, page in enumerate(doc):
    text = page.get_text()
    print(f"--- Page {i + 1} ({len(text)} caractères) ---")
    print(text[:300])
    print()

doc.close()