import asyncio
from typing import Optional, Dict, List
from app.core.gemini_client import call_gemini_with_image, GeminiAPIError


class ImageAnalyzer:
    """Analyze images using Gemini Vision API."""

    @staticmethod
    def analyze(
        image_base64: str,
        image_mime_type: str,
        page_num: Optional[int] = None,
    ) -> str:
        """
        Analyze a single image using Gemini Vision.

        Args:
            image_base64: Base64 encoded image
            image_mime_type: MIME type like 'image/png'
            page_num: Page number if from PDF

        Returns:
            Text description of image
        """
        try:
            prompt = (
                "Phân tích hình ảnh này chi tiết bằng tiếng Việt. "
                "Mô tả rõ: nội dung chính, các objects, text visible, layout, context."
            )
            if page_num:
                prompt += f"\n(Từ trang {page_num})"

            print(f"[IMAGE ANALYZER] Calling Gemini Vision (page: {page_num})")

            result = call_gemini_with_image(
                prompt=prompt,
                image_base64=image_base64,
                image_mime_type=image_mime_type,
                max_tokens=500,
                temperature=0.3,
            )

            return result if result else "Không thể phân tích ảnh"

        except GeminiAPIError as e:
            error_msg = f"Gemini API Error: {e}"
            print(f"[IMAGE ANALYZER] {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Error analyzing image: {e}"
            print(f"[IMAGE ANALYZER] {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg

    @staticmethod
    def analyze_batch(images: list) -> Dict[int, str]:
        """
        Analyze multiple images.

        Args:
            images: List of image dicts with 'data', 'format', 'index', 'page'

        Returns:
            Dict {image_index: description}
        """
        descriptions = {}

        for img_data in images:
            idx = img_data["index"]

            try:
                base64_data = img_data["data"]
                if "base64," in base64_data:
                    base64_data = base64_data.split("base64,")[1]

                fmt = img_data.get("format", "PNG").lower()
                mime_type = f"image/{fmt}" if fmt != "png" else "image/png"

                print(f"[IMAGE ANALYZER] Analyzing image {idx}...")

                description = ImageAnalyzer.analyze(
                    image_base64=base64_data,
                    image_mime_type=mime_type,
                    page_num=img_data.get("page"),
                )

                descriptions[idx] = description
                print(f"[IMAGE ANALYZER] Image {idx} ✓")

            except Exception as e:
                print(f"[IMAGE ANALYZER] Error image {idx}: {e}")
                descriptions[idx] = f"Lỗi phân tích: {e}"

        print(f"[IMAGE ANALYZER] Complete - {len(descriptions)} images analyzed")
        return descriptions
