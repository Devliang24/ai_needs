"""Image VL extraction result caching."""

import json
import hashlib
import logging
from typing import Optional
from pathlib import Path

from app.cache.redis_client import redis_client

logger = logging.getLogger(__name__)

# 缓存键前缀
CACHE_PREFIX = "vl_extract"
# 默认缓存时间：7天（秒）
DEFAULT_TTL = 7 * 24 * 60 * 60


def get_image_hash(image_path: str | Path) -> str:
    """
    计算图片文件的SHA256哈希值。

    Args:
        image_path: 图片文件路径

    Returns:
        SHA256哈希值的十六进制字符串
    """
    sha256_hash = hashlib.sha256()
    with open(image_path, "rb") as f:
        # 读取并更新哈希
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


async def get_cached_extraction(image_path: str | Path, model: str) -> Optional[str]:
    """
    从缓存获取VL模型提取的结果。

    Args:
        image_path: 图片文件路径
        model: 使用的VL模型名称

    Returns:
        缓存的提取文本，如果不存在则返回None
    """
    try:
        # 计算图片哈希
        image_hash = get_image_hash(image_path)

        # 构建缓存键：包含模型名称以区分不同模型的结果
        cache_key = f"{CACHE_PREFIX}:{model}:{image_hash}"

        # 从Redis获取缓存
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            logger.info(f"Cache hit for image hash {image_hash[:8]}... with model {model}")
            # 解析JSON并返回文本
            data = json.loads(cached_data)
            return data.get("extracted_text")
        else:
            logger.info(f"Cache miss for image hash {image_hash[:8]}... with model {model}")
            return None

    except Exception as e:
        logger.warning(f"Failed to get cached extraction: {e}")
        return None


async def cache_extraction(
    image_path: str | Path,
    model: str,
    extracted_text: str,
    ttl: int = DEFAULT_TTL
) -> bool:
    """
    缓存VL模型提取的结果。

    Args:
        image_path: 图片文件路径
        model: 使用的VL模型名称
        extracted_text: 提取的文本
        ttl: 缓存时间（秒）

    Returns:
        是否缓存成功
    """
    try:
        # 计算图片哈希
        image_hash = get_image_hash(image_path)

        # 构建缓存键
        cache_key = f"{CACHE_PREFIX}:{model}:{image_hash}"

        # 准备缓存数据
        cache_data = {
            "extracted_text": extracted_text,
            "model": model,
            "image_hash": image_hash,
            "text_length": len(extracted_text)
        }

        # 存储到Redis
        await redis_client.set(
            cache_key,
            json.dumps(cache_data, ensure_ascii=False),
            ex=ttl
        )

        logger.info(
            f"Cached extraction for image hash {image_hash[:8]}... "
            f"with model {model}, TTL: {ttl}s"
        )
        return True

    except Exception as e:
        logger.warning(f"Failed to cache extraction: {e}")
        return False


async def invalidate_cache(image_path: str | Path, model: Optional[str] = None) -> bool:
    """
    使缓存失效。

    Args:
        image_path: 图片文件路径
        model: 可选的模型名称，如果提供则只删除该模型的缓存

    Returns:
        是否删除成功
    """
    try:
        # 计算图片哈希
        image_hash = get_image_hash(image_path)

        if model:
            # 删除特定模型的缓存
            cache_key = f"{CACHE_PREFIX}:{model}:{image_hash}"
            deleted = await redis_client.delete(cache_key)
            logger.info(f"Deleted cache for model {model}, image hash {image_hash[:8]}...")
        else:
            # 删除所有模型的缓存
            # 使用pattern匹配所有相关的键
            pattern = f"{CACHE_PREFIX}:*:{image_hash}"
            keys = []
            async for key in redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await redis_client.delete(*keys)
                logger.info(f"Deleted {deleted} cache entries for image hash {image_hash[:8]}...")
            else:
                deleted = 0

        return deleted > 0

    except Exception as e:
        logger.warning(f"Failed to invalidate cache: {e}")
        return False