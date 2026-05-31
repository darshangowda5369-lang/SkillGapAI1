import os
from PyPDF2 import PdfReader

class PDFService:
    @staticmethod
    def extract_text(file_path):
        """
        Extracts text from a given file path. Supports .pdf and .txt files.
        """
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Failed to read TXT file: {str(e)}")
                
        elif ext == '.pdf':
            try:
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                if not text.strip():
                    raise ValueError("PDF file appears to be empty or contains only scanned images (no selectable text).")
                return text
            except Exception as e:
                raise ValueError(f"Failed to parse PDF file: {str(e)}")
                
        elif ext == '.docx':
            try:
                import docx
                doc = docx.Document(file_path)
                text = ""
                for para in doc.paragraphs:
                    if para.text:
                        text += para.text + "\n"
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.text:
                                text += cell.text + " "
                        text += "\n"
                
                if not text.strip():
                    raise ValueError("DOCX file appears to be empty.")
                return text
            except Exception as e:
                raise ValueError(f"Failed to parse DOCX file: {str(e)}")
        else:
            raise ValueError(f"Unsupported file format: {ext}. Only PDF, DOCX, and TXT files are supported.")
