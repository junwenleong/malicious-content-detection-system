import os
import time
from typing import Any, Dict, List, Optional, Tuple

import joblib


class Predictor:
    def __init__(self, model_path: str, config_path: str) -> None:
        if not os.path.exists(model_path) or not os.path.exists(config_path):
            raise FileNotFoundError("Model files not found. Train the model first.")

        self.model = joblib.load(model_path)
        self.config: Dict[str, Any] = joblib.load(config_path)
        pos_class = self.config["positive_class"]
        self.pos_index = list(self.model.classes_).index(pos_class)

    def predict(
        self, texts: List[str], threshold: Optional[float] = None
    ) -> Tuple[List[str], List[float], float]:
        start_time = time.time()
        probs = self.model.predict_proba(texts)[:, self.pos_index]
        effective_threshold = (
            float(threshold)
            if threshold is not None
            else float(self.config["optimal_threshold"])
        )
        labels = ["MALICIOUS" if p >= effective_threshold else "BENIGN" for p in probs]
        latency = time.time() - start_time
        return labels, probs.tolist(), latency

    async def apredict(
        self, texts: List[str], threshold: Optional[float] = None
    ) -> Tuple[List[str], List[float], float]:
        import asyncio

        return await asyncio.to_thread(self.predict, texts, threshold)
