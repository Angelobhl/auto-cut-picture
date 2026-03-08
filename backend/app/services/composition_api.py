import httpx
from typing import Optional, List, Dict
from ..models import AspectRatio, CropData, AnalysisResult, AnalyzeResponse
from ..config.settings import settings
import logging
import base64
import json
import re

logger = logging.getLogger(__name__)


class CompositionAPI:
    """
    Smart composition API service using qwen3-vl-plus (阿里云百炼).
    """

    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.api_url = settings.QWEN_API_URL
        self.model = settings.QWEN_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)

    async def analyze_image(
        self,
        image_path: str,
        image_id: str,
        aspect_ratios: Optional[List[AspectRatio]] = None
    ) -> AnalyzeResponse:
        """
        Analyze an image and suggest crop areas for different aspect ratios using qwen3-vl-plus.

        Args:
            image_path: Path to image file
            image_id: ID of the image
            aspect_ratios: List of aspect ratios to analyze

        Returns:
            AnalyzeResponse with suggested crop areas
        """
        # Default aspect ratios if none provided
        if not aspect_ratios:
            aspect_ratios = [
                AspectRatio(width=1, height=1),
                AspectRatio(width=16, height=9),
                AspectRatio(width=9, height=16),
            ]

        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Get image dimensions
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_data))
            img_width, img_height = image.size

            # Use qwen3-vl-plus for analysis
            results = await self._analyze_with_qwen(
                image_data, img_width, img_height, aspect_ratios
            )

            return AnalyzeResponse(
                imageId=image_id,
                results=results
            )

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return fallback centered crops
            return self._get_fallback_analysis(image_id, aspect_ratios, img_width, img_height)

    async def _analyze_with_qwen(
        self,
        image_data: bytes,
        img_width: int,
        img_height: int,
        aspect_ratios: List[AspectRatio]
    ) -> List[AnalysisResult]:
        """
        Analyze using qwen3-vl-plus (阿里云百炼).
        API: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
        """
        try:
            # Convert image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')

            # Build aspect ratio descriptions for the prompt
            ratio_descriptions = []
            for ar in aspect_ratios:
                ratio_descriptions.append(f"- {ar.width}:{ar.height}")

            # Build the prompt for qwen3-vl-plus
            system_prompt = """你是一个专业的图片构图分析助手。请分析这张图片的主要内容，并为指定的宽高比推荐最佳的裁剪区域。

请以 JSON 格式返回结果，格式如下：
```json
{
  "analysis": "简短描述图片的主要内容",
  "focus_areas": [
    {"x": 10, "y": 15, "width": 20, "height": 25, "description": "主体描述"}
  ],
  "crops": [
    {"ratio": "1:1", "x": 5.5, "y": 3.2, "width": 89.0, "height": 89.0, "reason": "构图原因"}
  ]
}
```

其中：
- x, y: 裁剪区域左上角的坐标（百分比，0-100）
- width, height: 裁剪区域的宽度和高度（百分比，0-100）
- 所有坐标值都应该是百分比形式，范围 0-100，保留1位小数
- ratio: 宽高比，如 "1:1", "16:9"
- reason: 简要说明为什么这样裁剪

注意：
1. 确保裁剪区域包含图片的主要主体
2. 裁剪区域应在图片范围内
3. 优先遵循构图原则（三分法、黄金分割等）
4. 确保推荐的裁剪区域符合指定的宽高比"""

            user_prompt = f"""请分析这张图片，为以下宽高比推荐最佳裁剪区域：
{chr(10).join(ratio_descriptions)}

图片尺寸：{img_width}x{img_height} 像素

请返回 JSON 格式的结果。"""

            # Build request for qwen3-vl-plus (OpenAI-compatible format)
            model_name = self.model or "qwen3-vl-plus"
            api_endpoint = self.api_url or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": system_prompt
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                # "temperature": 0.3,
                # "max_tokens": 2000
            }

            # Make API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            logger.info(f"Calling qwen3-vl-plus API: {api_endpoint}, model: {model_name}, headers: {headers}")

            response = await self.client.post(
                api_endpoint,
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"qwen3-vl-plus response: {json.dumps(data, ensure_ascii=False)[:500]}...")

            # Parse response
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Extract JSON from response (handle markdown code blocks)
            json_str = self._extract_json_from_response(content)

            if not json_str:
                logger.warning(f"Could not extract JSON from Qwen response: {content}")
                # Fallback to local algorithm
                return self._get_local_crops(img_width, img_height, aspect_ratios)

            try:
                result = json.loads(json_str)
                logger.info(f"Parsed result: {result}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from response: {e}")
                return self._get_local_crops(img_width, img_height, aspect_ratios)

            # Build results from parsed data
            results = []
            crops = result.get("crops", [])

            for idx, ar in enumerate(aspect_ratios):
                version_id = f"v{idx+1}"

                # Find matching crop from response
                crop_data = None
                reason = ""

                for crop in crops:
                    if self._ratio_matches(crop.get("ratio", ""), ar):
                        crop_data = crop
                        reason = crop.get("reason", "")
                        break

                if crop_data:
                    # Validate crop data
                    x = max(0, min(100, float(crop_data.get("x", 0))))
                    y = max(0, min(100, float(crop_data.get("y", 0))))
                    width = max(1, min(100, float(crop_data.get("width", 100))))
                    height = max(1, min(100, float(crop_data.get("height", 100))))

                    name = f"Qwen {ar.width}:{ar.height}"
                    if reason:
                        name += f" - {reason[:30]}..."
                else:
                    # Fallback if no matching crop found
                    logger.warning(f"No crop found for ratio {ar.width}:{ar.height}")
                    local_crop = self._calculate_smart_crop_local(
                        img_width, img_height, ar.width, ar.height
                    )
                    x, y, width, height = local_crop["x"], local_crop["y"], local_crop["width"], local_crop["height"]
                    name = f"Smart {ar.width}:{ar.height}"

                results.append(
                    AnalysisResult(
                        versionId=version_id,
                        name=name,
                        cropData=CropData(x=x, y=y, width=width, height=height)
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Qwen API error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _extract_json_from_response(self, content: str) -> Optional[str]:
        """Extract JSON string from response, handling markdown code blocks."""
        # Try to extract JSON from markdown code block
        json_block_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_block_match:
            return json_block_match.group(1).strip()

        # Try to extract JSON from regular code block
        code_block_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
        if code_block_match:
            content_to_parse = code_block_match.group(1).strip()
            try:
                json.loads(content_to_parse)
                return content_to_parse
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in the content
        json_obj_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_obj_match:
            json_str = json_obj_match.group(0)
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass

        return None

    def _ratio_matches(self, ratio_str: str, aspect_ratio: AspectRatio) -> bool:
        """Check if a ratio string matches the aspect ratio."""
        if not ratio_str:
            return False

        # Normalize ratio string
        ratio_str = ratio_str.replace("：", ":").replace(" ", "").replace("\u200b", "")

        # Expected format
        expected = f"{aspect_ratio.width}:{aspect_ratio.height}"

        return ratio_str == expected

    def _get_local_crops(
        self,
        img_width: int,
        img_height: int,
        aspect_ratios: List[AspectRatio]
    ) -> List[AnalysisResult]:
        """Get local algorithm crops as fallback."""
        results = []
        for idx, ar in enumerate(aspect_ratios):
            version_id = f"v{idx+1}"
            crop_data = self._calculate_smart_crop_local(
                img_width, img_height,
                ar.width, ar.height
            )
            name = f"Smart {ar.width}:{ar.height}"
            results.append(
                AnalysisResult(
                    versionId=version_id,
                    name=name,
                    cropData=CropData(**crop_data)
                )
            )
        return results

    def _calculate_smart_crop_local(
        self,
        img_width: int,
        img_height: int,
        target_ratio_w: int,
        target_ratio_h: int
    ) -> Dict[str, float]:
        """Calculate smart crop area using local algorithm (rule of thirds)."""
        target_ratio = target_ratio_w / target_ratio_h
        image_ratio = img_width / img_height

        if image_ratio > target_ratio:
            crop_height = img_height
            crop_width = int(crop_height * target_ratio)
            x_offset = (img_width - crop_width) // 3
            x = x_offset
            y = 0
        else:
            crop_width = img_width
            crop_height = int(crop_width / target_ratio)
            y_offset = (img_height - crop_height) // 3
            x = 0
            y = y_offset

        return {
            "x": (x / img_width) * 100,
            "y": (y / img_height) * 100,
            "width": (crop_width / img_width) * 100,
            "height": (crop_height / img_height) * 100
        }

    def _get_fallback_analysis(
        self,
        image_id: str,
        aspect_ratios: List[AspectRatio],
        img_width: int,
        img_height: int
    ) -> AnalyzeResponse:
        """Return fallback centered crops if analysis fails."""
        results = []

        for idx, ar in enumerate(aspect_ratios):
            version_id = f"v{idx+1}"

            target_ratio = ar.width / ar.height
            image_ratio = img_width / img_height

            if image_ratio > target_ratio:
                crop_height = img_height
                crop_width = int(crop_height * target_ratio)
                x = (img_width - crop_width) // 2
                y = 0
            else:
                crop_width = img_width
                crop_height = int(crop_width / target_ratio)
                x = 0
                y = (img_height - crop_height) // 2

            crop_data = {
                "x": (x / img_width) * 100,
                "y": (y / img_height) * 100,
                "width": (crop_width / img_width) * 100,
                "height": (crop_height / img_height) * 100
            }

            results.append(
                AnalysisResult(
                    versionId=version_id,
                    name=f"{ar.width}:{ar.height}",
                    cropData=CropData(**crop_data)
                )
            )

        return AnalyzeResponse(
            imageId=image_id,
            results=results
        )

    async def close(self) -> None:
        """Close the HTTP client"""
        await self.client.aclose()
