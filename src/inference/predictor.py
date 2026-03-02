import asyncio
import os
import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict
import threading

import joblib

from src.inference.base import BasePredictor
from src.config import settings
from src.utils.text import normalize_text


class Predictor(BasePredictor):
    def __init__(
        self, model_path: str, config_path: str, cache_size: int | None = None
    ) -> None:
        """Initialize predictor with model loading and cache setup.

        Args:
            model_path: Path to trained model file (.pkl)
            config_path: Path to model configuration file (.pkl)
            cache_size: LRU cache size (defaults to settings value)

        Raises:
            FileNotFoundError: If model files don't exist
            ValueError: If model integrity check fails
        """
        if not os.path.exists(model_path) or not os.path.exists(config_path):
            raise FileNotFoundError("Model files not found. Train the model first.")

        # Verify integrity before loading (prevents loading tampered models)
        self._verify_checksum(model_path, settings.model_sha256)
        self._verify_checksum(config_path, settings.config_sha256)

        self.model = joblib.load(model_path)
        self.config: Dict[str, Any] = joblib.load(config_path)
        pos_class = self.config["positive_class"]
        self.pos_index = list(self.model.classes_).index(pos_class)

        # LRU cache for repeated queries (common in abuse campaigns)
        # Size limit prevents memory leaks from unique adversarial inputs
        self._cache: OrderedDict[str, float] = OrderedDict()
        self._cache_size = cache_size or settings.prediction_cache_size
        self._lock = threading.Lock()

        # Cache statistics for monitoring
        self._cache_hits = 0
        self._cache_misses = 0

    def _cache_key(self, text: str) -> str:
        """Generate a SHA256 cache key for text.

        Always hashes the text to avoid storing plaintext in cache memory,
        which could expose sensitive content in heap dumps or memory profiling.

        Args:
            text: Input text to generate key for

        Returns:
            SHA256 hex digest of the text
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _get_from_cache(self, text: str) -> Optional[float]:
        """Retrieve probability from cache if available.

        Args:
            text: Input text to look up

        Returns:
            Cached probability or None if not found
        """
        key = self._cache_key(text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)  # LRU: mark as recently used
                self._cache_hits += 1
                return self._cache[key]
            self._cache_misses += 1
            return None

    def _add_to_cache(self, text: str, prob: float) -> None:
        """Add prediction to cache with LRU eviction.

        Args:
            text: Input text
            prob: Predicted probability
        """
        key = self._cache_key(text)
        with self._lock:
            self._cache[key] = prob
            self._cache.move_to_end(key)

            # Evict oldest entry if cache is full
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary with cache metrics
        """
        with self._lock:
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0
            return {
                "cache_size": len(self._cache),
                "cache_max_size": self._cache_size,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate": hit_rate,
            }

    def clear_cache(self) -> None:
        """Clear the prediction cache.

        Useful after model updates or threshold changes.
        Also resets cache statistics.
        """
        with self._lock:
            self._cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0

    def _verify_checksum(self, file_path: str, expected_hash: str) -> None:
        """Verify file integrity using SHA256 checksum.

        This prevents loading tampered or corrupted model files.
        The system will refuse to start if checksums don't match.

        Args:
            file_path: Path to file to verify
            expected_hash: Expected SHA256 hash

        Raises:
            ValueError: If checksum doesn't match expected value
        """
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

    def _normalize_text(self, text: str) -> str:
        """Normalize text using the shared utility.

        Delegates to src.utils.text.normalize_text to ensure training and
        inference use identical preprocessing. See that function for details.

        Args:
            text: Raw input text

        Returns:
            Normalized text safe for feature extraction
        """
        return normalize_text(text)

    def predict(
        self, texts: List[str], threshold: Optional[float] = None
    ) -> Tuple[List[str], List[float], float]:
        """Predict malicious content labels and probabilities for input texts.

        Args:
            texts: List of text strings to classify
            threshold: Optional decision threshold (uses model config if None)

        Returns:
            Tuple of (labels, probabilities, latency_seconds)

        Raises:
            RuntimeError: If prediction fails due to model error
        """
        # Edge case: Empty input
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
                    # Clamp probabilities to valid range [0, 1]
                    # Some calibration methods can produce values slightly outside
                    clamped_prob = max(0.0, min(1.0, float(prob)))
                    probs[idx] = clamped_prob
                    self._add_to_cache(normalized_texts[idx], clamped_prob)
            except Exception as e:
                # Wrap obscure sklearn/joblib errors with context
                raise RuntimeError(
                    f"Prediction failed: {str(e)}. "
                    "This may indicate model corruption or incompatible input."
                ) from e

        # Apply threshold with defensive clamping
        effective_threshold = (
            float(threshold)
            if threshold is not None
            else float(self.config["optimal_threshold"])
        )

        # Clamp threshold to valid range
        effective_threshold = max(0.0, min(1.0, effective_threshold))

        labels = ["MALICIOUS" if p >= effective_threshold else "BENIGN" for p in probs]
        latency = time.monotonic() - start_time
        return labels, probs, latency

    async def apredict(
        self, texts: List[str], threshold: Optional[float] = None
    ) -> Tuple[List[str], List[float], float]:
        return await asyncio.to_thread(self.predict, texts, threshold)
