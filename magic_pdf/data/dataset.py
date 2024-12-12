import os
from abc import ABC, abstractmethod
from typing import Callable, Iterator

import fitz

from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.schemas import PageInfo
from magic_pdf.data.utils import fitz_doc_to_image
from magic_pdf.filter import classify


class PageableData(ABC):
    @abstractmethod
    def get_image(self) -> dict:
        """Transform data to image."""
        pass

    @abstractmethod
    def get_doc(self) -> fitz.Page:
        """Get the pymudoc page."""
        pass

    @abstractmethod
    def get_page_info(self) -> PageInfo:
        """Get the page info of the page.

        Returns:
            PageInfo: the page info of this page
        """
        pass

        @abstractmethod
    def draw_rect(self, rect_coords, color, fill, fill_opacity, width, overlay):
        pass

    @abstractmethod
    def insert_text(self, coord, content, fontsize, color):
        pass


class Dataset(ABC):
    @abstractmethod
    def __len__(self) -> int:
        """The length of the dataset."""
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[PageableData]:
        """Yield the page data."""
        pass

    @abstractmethod
    def supported_methods(self) -> list[SupportedPdfParseMethod]:
        """The methods that this dataset support.

        Returns:
            list[SupportedPdfParseMethod]: The supported methods, Valid methods are: OCR, TXT
        """
        pass

    @abstractmethod
    def data_bits(self) -> bytes:
        """The bits used to create this dataset."""
        pass

    @abstractmethod
    def get_page(self, page_id: int) -> PageableData:
        """Get the page indexed by page_id.

        Args:
            page_id (int): the index of the page

        Returns:
            PageableData: the page doc object
        """
        pass

        @abstractmethod
    def dump_to_file(self, file_path: str):
        pass

    @abstractmethod
    def apply(self, proc: Callable, *args, **kwargs):
        pass

    @abstractmethod
    def classify(self) -> SupportedPdfParseMethod:
        pass


class PymuDocDataset(Dataset):
    def __init__(self, bits: bytes):
        """Initialize the dataset, which wraps the pymudoc documents.

        Args:
            bits (bytes): the bytes of the pdf
        """
        self._raw_fitz = fitz.open('pdf', bits)
        self._records = [Doc(v) for v in self._raw_fitz]
        self._data_bits = bits
        self._raw_data = bits

    def __len__(self) -> int:
        """The page number of the pdf."""
        return len(self._records)

    def __iter__(self) -> Iterator[PageableData]:
        """Yield the page doc object."""
        return iter(self._records)

    def supported_methods(self) -> list[SupportedPdfParseMethod]:
        """The method supported by this dataset.

        Returns:
            list[SupportedPdfParseMethod]: the supported methods
        """
        return [SupportedPdfParseMethod.OCR, SupportedPdfParseMethod.TXT]

    def data_bits(self) -> bytes:
        """The pdf bits used to create this dataset."""
        return self._data_bits

    def get_page(self, page_id: int) -> PageableData:
        """The page doc object.

        Args:
            page_id (int): the page doc index

        Returns:
            PageableData: the page doc object
        """
        return self._records[page_id]

        def dump_to_file(self, file_path: str):
        dir_name = os.path.dirname(file_path)
        if dir_name not in ('', '.', '..'):
            os.makedirs(dir_name, exist_ok=True)
        self._raw_fitz.save(file_path)

    def apply(self, proc: Callable, *args, **kwargs):
        new_args = tuple([self] + list(args))
        return proc(*new_args, **kwargs)

    def classify(self) -> SupportedPdfParseMethod:
        return classify(self._data_bits)


class ImageDataset(Dataset):
    def __init__(self, bits: bytes):
        """Initialize the dataset, which wraps the pymudoc documents.

        Args:
            bits (bytes): the bytes of the photo which will be converted to pdf first. then converted to pymudoc.
        """
        pdf_bytes = fitz.open(stream=bits).convert_to_pdf()
        self._raw_fitz = fitz.open('pdf', pdf_bytes)
        self._records = [Doc(v) for v in self._raw_fitz]
        self._raw_data = bits
        self._data_bits = pdf_bytes

    def __len__(self) -> int:
        """The length of the dataset."""
        return len(self._records)

    def __iter__(self) -> Iterator[PageableData]:
        """Yield the page object."""
        return iter(self._records)

    def supported_methods(self):
        """The method supported by this dataset.

        Returns:
            list[SupportedPdfParseMethod]: the supported methods
        """
        return [SupportedPdfParseMethod.OCR]

    def data_bits(self) -> bytes:
        """The pdf bits used to create this dataset."""
        return self._data_bits

    def get_page(self, page_id: int) -> PageableData:
        """The page doc object.

        Args:
            page_id (int): the page doc index

        Returns:
            PageableData: the page doc object
        """
        return self._records[page_id]

        def dump_to_file(self, file_path: str):
        dir_name = os.path.dirname(file_path)
        if dir_name not in ('', '.', '..'):
            os.makedirs(dir_name, exist_ok=True)
        self._raw_fitz.save(file_path)

    def apply(self, proc: Callable, *args, **kwargs):
        return proc(self, *args, **kwargs)

    def classify(self) -> SupportedPdfParseMethod:
        return SupportedPdfParseMethod.OCR


class Doc(PageableData):
    """Initialized with pymudoc object."""

    def __init__(self, doc: fitz.Page):
        self._doc = doc

    def get_image(self):
        """Return the imge info.

        Returns:
            dict: {
                img: np.ndarray,
                width: int,
                height: int
            }
        """
        return fitz_doc_to_image(self._doc)

    def get_doc(self) -> fitz.Page:
        """Get the pymudoc object.

        Returns:
            fitz.Page: the pymudoc object
        """
        return self._doc

    def get_page_info(self) -> PageInfo:
        """Get the page info of the page.

        Returns:
            PageInfo: the page info of this page
        """
        page_w = self._doc.rect.width
        page_h = self._doc.rect.height
        return PageInfo(w=page_w, h=page_h)

    def __getattr__(self, name):
        if hasattr(self._doc, name):
            return getattr(self._doc, name)

    def draw_rect(self, rect_coords, color, fill, fill_opacity, width, overlay):
        self._doc.draw_rect(
            rect_coords,
            color=color,
            fill=fill,
            fill_opacity=fill_opacity,
            width=width,
            overlay=overlay,
        )
        
    def insert_text(self, coord, content, fontsize, color):
        self._doc.insert_text(coord, content, fontsize=fontsize, color=color)