import pandas
import io
import PyPDF2

class FileProcessor:
    def __init__(self):
        self.extensions = {
            'pdf': self.process_pdf,
            'xml': self.process_xml,
            'csv': self.process_csv,
            'txt': self.process_txt
        }

    def process_pdf(self, content):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text

    def process_xml(self, content):
        return content.decode('UTF-8')

    def process_csv(self, content):
        csv_string = content.decode('UTF-8')
        df = pandas.read_csv(io.StringIO(csv_string))
        return df.to_string(index=False)

    def process_txt(self, content):
        return content.decode('UTF-8')

    def run(self, file_extension, content):
        handler = self.extensions.get(file_extension.lower())
        if not handler:
            raise ValueError(f"No handler for extension: {file_extension}")
        return handler(content)

file_handler = FileProcessor()