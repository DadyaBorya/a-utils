from io import BytesIO
from typing import List, Any
import base64

import PyPDF4
from PyPDF4.generic import NameObject
from PyPDF4.pdf import ContentStream
from PyPDF4.utils import b_
import fitz

from fastapi import UploadFile, HTTPException

from src.utils.decoder import Decoder


class HstsMvsProcess:
    async def process(self, file: UploadFile):
        content = await file.read()

        if not content or len(content) == 0:
            raise HTTPException(status_code=400, detail="PDF файл порожній")

        if not content.startswith(b'%PDF'):
            raise HTTPException(status_code=400, detail="Файл не є дійсним PDF документом")

        buffer = BytesIO(content)

        processed_file = self._remove_water_mark(buffer)
        processed_file.seek(0)
        processed_bytes = processed_file.read()

        images = self._extract_images(processed_bytes)

        if len(images) == 0:
            raise HTTPException(status_code=404, detail="Не знайдено зображення.")

        encoded_image = base64.b64encode(BytesIO(images[0]).getvalue()).decode("utf-8")
        encoded_pdf = base64.b64encode(processed_file.getvalue()).decode("utf-8")

        return encoded_pdf, encoded_image

    def _extract_images(self, buffer: bytes) -> List[bytes]:
        doc: fitz.Document = None
        try:
            image = []
            doc = fitz.open(stream=buffer, filetype="pdf")
            for page_index in range(len(doc)):
                page: fitz.Page = doc[page_index]
                images = page.get_images(full=True)
                for img in images:
                    xref: int = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes: bytes = base_image["image"]
                    image.append(image_bytes)

            return image
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Помилка при витягуванні зображень: {str(e)}")
        finally:
            if doc:
                doc.close()

    def _remove_water_mark(self, buffer: BytesIO):
        try:
            reader = PyPDF4.PdfFileReader(buffer)
            writer = PyPDF4.PdfFileWriter()
            total_pages = reader.getNumPages()
            for page_num in range(total_pages):
                page = reader.getPage(page_num)

                if "/Contents" not in page:
                    continue

                content_object = page["/Contents"].getObject()
                content_stream = ContentStream(content_object, reader)

                cleaned_operations = []

                for operands, operator in list(content_stream.operations):
                    if self._is_water_mark(operands, operator):
                        continue
                    cleaned_operations.append((operands, operator))

                content_stream.operations = cleaned_operations
                page[NameObject('/Contents')] = content_stream
                writer.addPage(page)

            output_buffer = BytesIO()
            writer.write(output_buffer)
            output_buffer.seek(0)
            return output_buffer
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Помилка при читанні PDF: {str(e)}")

    def _is_water_mark(self, operands: List[Any], operator: bytes):
        return (self._is_text_watermark(operands, operator) or
                self._is_image_watermark(operands, operator))

    def _is_text_watermark(self, operands: List[Any], operator: bytes) -> bool:
        if operator != b_("Tj") or not operands:
            return False

        text = Decoder.decode_text(operands[0])
        return any(watermark in text for watermark in ["Користувач "])

    def _is_image_watermark(self, operands: List[Any], operator: bytes) -> bool:
        if operator != b_("Do") or not operands:
            return False

        return operands[0] in "/I2"
