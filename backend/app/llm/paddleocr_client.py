"""PaddleOCR-VL client for local document parsing and OCR."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Global singleton instance to avoid repeated model loading
_pipeline: Optional[object] = None


def is_paddleocr_available() -> bool:
    """Check if PaddleOCR-VL is available in the environment.

    Returns:
        bool: True if paddleocr library is installed, False otherwise
    """
    try:
        import paddleocr  # noqa: F401
        return True
    except ImportError:
        logger.warning("PaddleOCR library not installed. Install with: pip install 'paddleocr[doc-parser]'")
        return False


def get_pipeline() -> object:
    """Get or create the global PaddleOCR-VL pipeline instance.

    Uses singleton pattern to avoid loading the model multiple times.
    First call may take several minutes to download the model.

    Returns:
        PaddleOCRVL: The pipeline instance

    Raises:
        ImportError: If paddleocr is not installed
        RuntimeError: If model initialization fails
    """
    global _pipeline

    if _pipeline is not None:
        return _pipeline

    if not is_paddleocr_available():
        raise ImportError(
            "PaddleOCR not available. Install with: pip install 'paddleocr[doc-parser]'"
        )

    try:
        from paddleocr import PaddleOCRVL

        logger.info("Initializing PaddleOCR-VL pipeline (first-time may download model)...")
        _pipeline = PaddleOCRVL()
        logger.info("PaddleOCR-VL pipeline initialized successfully")
        return _pipeline

    except Exception as e:
        logger.exception("Failed to initialize PaddleOCR-VL pipeline")
        raise RuntimeError(f"PaddleOCR-VL initialization failed: {e}") from e


def extract_requirements_from_image(
    image_path: str | Path,
    query: Optional[str] = None,
) -> str:
    """Extract text and structured content from an image using PaddleOCR-VL.

    This function uses PaddleOCR-VL-0.9B model for local document parsing.
    The model excels at recognizing complex elements including text, tables,
    formulas, and charts in 109 languages.

    Args:
        image_path: Path to the image file (PNG, JPG, JPEG, BMP)
        query: Optional question/prompt for VQA-style extraction.
               Default: extracts all content as markdown

    Returns:
        str: Extracted text content in markdown format

    Raises:
        ImportError: If PaddleOCR is not installed
        RuntimeError: If model inference fails
        FileNotFoundError: If image_path does not exist
    """
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    pipeline = get_pipeline()

    try:
        # Prepare input
        if query:
            # VQA-style extraction with custom query
            input_data = {
                'image': str(image_path),
                'query': query
            }
        else:
            # Direct image path for full content extraction
            input_data = str(image_path)

        logger.info(f"Running PaddleOCR-VL inference on {image_path.name}")
        output = pipeline.predict(input_data)

        # Extract text from results
        extracted_texts = []
        for res in output:
            # Try to get markdown format (preserves table structure)
            if hasattr(res, 'to_markdown'):
                text = res.to_markdown()
            elif hasattr(res, 'to_text'):
                text = res.to_text()
            else:
                # Fallback to string representation
                text = str(res)

            if text and text.strip():
                extracted_texts.append(text.strip())

        full_text = "\n\n".join(extracted_texts)

        if not full_text.strip():
            logger.warning(f"No text extracted from {image_path.name}")
            return ""

        logger.info(
            f"Successfully extracted {len(full_text)} characters from {image_path.name}"
        )
        return full_text

    except Exception as e:
        logger.exception(f"PaddleOCR-VL inference failed for {image_path}")
        raise RuntimeError(f"Failed to extract text from image: {e}") from e


def extract_requirements_from_image_batch(
    image_paths: list[str | Path],
    query: Optional[str] = None,
) -> list[str]:
    """Extract text from multiple images in batch mode (memory efficient).

    Uses iterator mode for better memory management with large datasets.

    Args:
        image_paths: List of image file paths
        query: Optional question/prompt for VQA-style extraction

    Returns:
        list[str]: List of extracted text for each image

    Raises:
        ImportError: If PaddleOCR is not installed
        RuntimeError: If model inference fails
    """
    pipeline = get_pipeline()

    try:
        # Prepare inputs
        if query:
            inputs = [
                {'image': str(path), 'query': query}
                for path in image_paths
            ]
        else:
            inputs = [str(path) for path in image_paths]

        logger.info(f"Running PaddleOCR-VL batch inference on {len(inputs)} images")

        # Use predict_iter for memory efficiency
        results = []
        for idx, res in enumerate(pipeline.predict_iter(inputs)):
            if hasattr(res, 'to_markdown'):
                text = res.to_markdown()
            elif hasattr(res, 'to_text'):
                text = res.to_text()
            else:
                text = str(res)

            results.append(text.strip() if text else "")
            logger.debug(f"Processed image {idx + 1}/{len(inputs)}")

        logger.info(f"Batch inference completed: {len(results)} results")
        return results

    except Exception as e:
        logger.exception("PaddleOCR-VL batch inference failed")
        raise RuntimeError(f"Failed to process image batch: {e}") from e


# Async wrapper for use in FastAPI
async def extract_requirements_from_image_async(
    image_path: str | Path,
    query: Optional[str] = None,
) -> str:
    """Async wrapper for extract_requirements_from_image.

    Runs the synchronous PaddleOCR inference in a thread pool
    to avoid blocking the event loop.

    Args:
        image_path: Path to the image file
        query: Optional question/prompt for VQA-style extraction

    Returns:
        str: Extracted text content
    """
    import asyncio

    return await asyncio.to_thread(
        extract_requirements_from_image,
        image_path,
        query
    )
