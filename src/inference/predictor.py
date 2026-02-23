import os
import re
import time
import hashlib
import unicodedata
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict
import threading

import joblib

from src.inference.base import BasePredictor
from src.config import settings


class Predictor(BasePredictor):
    def __init__(self, model_path: str, config_path: str) -> None:
        if not os.path.exists(model_path) or not os.path.exists(config_path):
            raise FileNotFoundError("Model files not found. Train the model first.")

        # Verify integrity
        self._verify_checksum(model_path, settings.model_sha256)
        self._verify_checksum(config_path, settings.config_sha256)

        self.model = joblib.load(model_path)
        self.config: Dict[str, Any] = joblib.load(config_path)
        pos_class = self.config["positive_class"]
        self.pos_index = list(self.model.classes_).index(pos_class)

        # Simple LRU cache: text -> probability
        # Limit size to prevent memory leaks
        self._cache: OrderedDict[str, float] = OrderedDict()
        self._cache_size = 10000
        self._lock = threading.Lock()

    def _cache_key(self, text: str) -> str:
        """Generate a cache key. Use hash for long texts to avoid memory bloat."""
        if len(text) > 512:
            return hashlib.sha256(text.encode("utf-8")).hexdigest()
        return text

    def _get_from_cache(self, text: str) -> Optional[float]:
        key = self._cache_key(text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
        return None

    def _add_to_cache(self, text: str, prob: float) -> None:
        key = self._cache_key(text)
        with self._lock:
            self._cache[key] = prob
            self._cache.move_to_end(key)
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)

    def clear_cache(self) -> None:
        """Clear the prediction cache. Useful after model updates or threshold changes."""
        with self._lock:
            self._cache.clear()

    def _verify_checksum(self, file_path: str, expected_hash: str) -> None:
        """Verify file integrity to prevent loading tampered models."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        calculated_hash = sha256_hash.hexdigest()
        if calculated_hash != expected_hash:
            raise ValueError(
                f"Integrity check failed for {file_path}. "
                f"Expected {expected_hash}, got {calculated_hash}"
            )

    # Compiled regex for stripping control characters
    _CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

    def _normalize_text(self, text: str) -> str:
        """Normalize text to NFKC form and strip control characters."""
        normalized = unicodedata.normalize("NFKC", text)
        normalized = self._CONTROL_CHAR_RE.sub("", normalized)
        return normalized

    def predict(
        self, texts: List[str], threshold: Optional[float] = None
    ) -> Tuple[List[str], List[float], float]:
        if not texts:
            return [], [], 0.0

        start_time = time.monotonic()

        # Sanitize input
        normalized_texts = [self._normalize_text(t) for t in texts]

        # Check cache
        probs = [0.0] * len(normalized_texts)
        miss_indices = []
        miss_texts = []

        for i, text in enumerate(normalized_texts):
            cached_prob = self._get_from_cache(text)
            if cached_prob is not None:
                probs[i] = cached_prob
            else:
                miss_indices.append(i)
                miss_texts.append(text)

        # Predict for misses
        if miss_texts:
            try:
                miss_probs = self.model.predict_proba(miss_texts)[:, self.pos_index]
                for idx, prob in zip(miss_indices, miss_probs):
                    probs[idx] = float(prob)
                    self._add_to_cache(normalized_texts[idx], float(prob))
            except Exception as e:
                # Wrap obscure sklearn/joblib errors
                raise RuntimeError(f"Prediction failed: {str(e)}") from e

        effective_threshold = (
            float(threshold)
            if threshold is not None
            else float(self.config["optimal_threshold"])
        )
        labels = ["MALICIOUS" if p >= effective_threshold else "BENIGN" for p in probs]
        latency = time.monotonic() - start_time
        return labels, probs, latency

    async def apredict(
        self, texts: List[str], threshold: Optional[float] = None
    ) -> Tuple[List[str], List[float], float]:
        import asyncio

        return await asyncio.to_thread(self.predict, texts, threshold)
