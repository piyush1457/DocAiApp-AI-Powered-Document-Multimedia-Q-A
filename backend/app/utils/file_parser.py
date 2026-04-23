import pdfplumber
import fitz  # PyMuPDF
from typing import List, Dict
from app.core.exceptions import IngestionError

def parse_pdf(file_path: str) -> List[Dict]:
    """
    Parses a PDF file and extracts text page by page.
    Uses pdfplumber as primary extractor and PyMuPDF as fallback.
    """
    results = []
    
    try:
        # Try with pdfplumber first
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    results.append({
                        "text": text.strip(),
                        "page_number": i + 1,
                        "char_count": len(text.strip())
                    })
        
        # If no text extracted, try PyMuPDF (scanned PDF fallback)
        if not results:
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                text = page.get_text()
                if text and text.strip():
                    results.append({
                        "text": text.strip(),
                        "page_number": i + 1,
                        "char_count": len(text.strip())
                    })
            doc.close()
            
        if not results:
            raise IngestionError("Could not extract any text from PDF. The file might be corrupted or empty.")
            
        return results
        
    except Exception as e:
        if isinstance(e, IngestionError):
            raise e
        raise IngestionError(f"Failed to parse PDF: {str(e)}")
