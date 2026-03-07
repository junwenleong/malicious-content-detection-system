"""Load testing for performance validation."""

import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

API_URL = "http://localhost:8000"
API_KEY = "test-key-12345678901234567890123456789012"

# Test configurations
SINGLE_PREDICTION_LOAD = 100  # Number of single predictions
BATCH_SIZE = 50  # Items per batch
BATCH_LOAD = 10  # Number of batches
CONCURRENT_WORKERS = 10  # Concurrent requests

# Performance thresholds
LATENCY_P50_THRESHOLD = 10  # ms
LATENCY_P95_THRESHOLD = 50  # ms
LATENCY_P99_THRESHOLD = 200  # ms
ERROR_RATE_THRESHOLD = 0.01  # 1%


def single_prediction_load_test() -> bool:
    """Test single prediction performance under load."""
    print("\n" + "=" * 80)
    print("SINGLE PREDICTION LOAD TEST")
    print("=" * 80)
    print(f"Sending {SINGLE_PREDICTION_LOAD} single predictions...")

    latencies = []
    errors = 0

    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = []

        for i in range(SINGLE_PREDICTION_LOAD):
            text = f"Test prompt {i}: How do I bake a cake?"
            future = executor.submit(
                _make_prediction,
                text,
            )
            futures.append(future)

        for i, future in enumerate(as_completed(futures)):
            try:
                latency = future.result()
                latencies.append(latency)
                if (i + 1) % 20 == 0:
                    print(f"  Completed {i + 1}/{SINGLE_PREDICTION_LOAD}")
            except Exception:
                errors += 1

    # Calculate statistics
    if latencies:
        latencies.sort()
        p50 = statistics.median(latencies)
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg = statistics.mean(latencies)
        error_rate = errors / (SINGLE_PREDICTION_LOAD + errors)

        print("\nResults:")
        print(f"  Total requests: {len(latencies) + errors}")
        print(f"  Successful: {len(latencies)}")
        print(f"  Errors: {errors}")
        print(f"  Error rate: {error_rate:.2%}")
        print("\nLatency (ms):")
        print(f"  p50: {p50:.2f}")
        print(f"  p95: {p95:.2f}")
        print(f"  p99: {p99:.2f}")
        print(f"  avg: {avg:.2f}")
        print(f"  min: {min(latencies):.2f}")
        print(f"  max: {max(latencies):.2f}")

        # Check thresholds
        passed = True
        if p50 > LATENCY_P50_THRESHOLD:
            print(
                f"\n⚠️  p50 latency {p50:.2f}ms exceeds threshold {LATENCY_P50_THRESHOLD}ms"
            )
            passed = False
        if p95 > LATENCY_P95_THRESHOLD:
            print(
                f"⚠️  p95 latency {p95:.2f}ms exceeds threshold {LATENCY_P95_THRESHOLD}ms"
            )
            passed = False
        if p99 > LATENCY_P99_THRESHOLD:
            print(
                f"⚠️  p99 latency {p99:.2f}ms exceeds threshold {LATENCY_P99_THRESHOLD}ms"
            )
            passed = False
        if error_rate > ERROR_RATE_THRESHOLD:
            print(
                f"⚠️  Error rate {error_rate:.2%} exceeds threshold {ERROR_RATE_THRESHOLD:.2%}"
            )
            passed = False

        if passed:
            print("\n✅ All thresholds passed!")
        else:
            print("\n❌ Some thresholds exceeded")

        return passed

    return False


def batch_prediction_load_test() -> bool:
    """Test batch prediction performance under load."""
    print("\n" + "=" * 80)
    print("BATCH PREDICTION LOAD TEST")
    print("=" * 80)
    print(f"Sending {BATCH_LOAD} batches of {BATCH_SIZE} items...")

    latencies = []
    errors = 0

    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = []

        for batch_num in range(BATCH_LOAD):
            texts = [f"Batch {batch_num} item {i}" for i in range(BATCH_SIZE)]
            future = executor.submit(
                _make_batch_prediction,
                texts,
            )
            futures.append(future)

        for i, future in enumerate(as_completed(futures)):
            try:
                latency = future.result()
                latencies.append(latency)
                print(f"  Completed batch {i + 1}/{BATCH_LOAD}")
            except Exception as e:
                errors += 1
                print(f"  Error: {e}")

    # Calculate statistics
    if latencies:
        latencies.sort()
        p50 = statistics.median(latencies)
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg = statistics.mean(latencies)
        error_rate = errors / (BATCH_LOAD + errors)
        throughput = (BATCH_LOAD * BATCH_SIZE) / (sum(latencies) / 1000)

        print("\nResults:")
        print(f"  Total batches: {len(latencies) + errors}")
        print(f"  Successful: {len(latencies)}")
        print(f"  Errors: {errors}")
        print(f"  Error rate: {error_rate:.2%}")
        print(f"  Total items processed: {len(latencies) * BATCH_SIZE}")
        print(f"  Throughput: {throughput:.0f} items/sec")
        print("\nLatency per batch (ms):")
        print(f"  p50: {p50:.2f}")
        print(f"  p95: {p95:.2f}")
        print(f"  p99: {p99:.2f}")
        print(f"  avg: {avg:.2f}")
        print(f"  min: {min(latencies):.2f}")
        print(f"  max: {max(latencies):.2f}")

        # Check thresholds
        passed = True
        if error_rate > ERROR_RATE_THRESHOLD:
            print(
                f"\n⚠️  Error rate {error_rate:.2%} exceeds threshold {ERROR_RATE_THRESHOLD:.2%}"
            )
            passed = False

        if passed:
            print("\n✅ All thresholds passed!")
        else:
            print("\n❌ Some thresholds exceeded")

        return passed

    return False


def sustained_load_test(duration_seconds: int = 60) -> bool:
    """Test sustained load over time."""
    print("\n" + "=" * 80)
    print(f"SUSTAINED LOAD TEST ({duration_seconds}s)")
    print("=" * 80)
    print(f"Sending predictions for {duration_seconds} seconds...")

    latencies = []
    errors = 0
    start_time = time.time()
    request_count = 0

    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = []

        while time.time() - start_time < duration_seconds:
            text = f"Sustained load test {request_count}"
            future = executor.submit(_make_prediction, text)
            futures.append(future)
            request_count += 1

            # Process completed futures
            done_futures = [f for f in futures if f.done()]
            for future in done_futures:
                try:
                    latency = future.result()
                    latencies.append(latency)
                except Exception:
                    errors += 1
                futures.remove(future)

            # Print progress every 10 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                print(
                    f"  {int(elapsed)}s: {len(latencies)} successful, {errors} errors"
                )

        # Wait for remaining futures
        for future in futures:
            try:
                latency = future.result()
                latencies.append(latency)
            except Exception:
                errors += 1

    # Calculate statistics
    elapsed = time.time() - start_time
    if latencies:
        latencies.sort()
        p50 = statistics.median(latencies)
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        avg = statistics.mean(latencies)
        error_rate = errors / (len(latencies) + errors)
        throughput = len(latencies) / elapsed

        print("\nResults:")
        print(f"  Duration: {elapsed:.1f}s")
        print(f"  Total requests: {len(latencies) + errors}")
        print(f"  Successful: {len(latencies)}")
        print(f"  Errors: {errors}")
        print(f"  Error rate: {error_rate:.2%}")
        print(f"  Throughput: {throughput:.1f} req/sec")
        print("\nLatency (ms):")
        print(f"  p50: {p50:.2f}")
        print(f"  p95: {p95:.2f}")
        print(f"  p99: {p99:.2f}")
        print(f"  avg: {avg:.2f}")

        passed = error_rate <= ERROR_RATE_THRESHOLD
        if passed:
            print("\n✅ Sustained load test passed!")
        else:
            print("\n❌ Error rate exceeded threshold")

        return passed

    return False


def _make_prediction(text: str) -> float:
    """Make a single prediction and return latency in ms."""
    start = time.time()
    response = requests.post(
        f"{API_URL}/v1/predict",
        json={"texts": [text]},
        headers={"x-api-key": API_KEY},
        timeout=10,
    )
    latency_ms = (time.time() - start) * 1000
    response.raise_for_status()
    return latency_ms


def _make_batch_prediction(texts: list[str]) -> float:
    """Make a batch prediction and return latency in ms."""
    start = time.time()
    response = requests.post(
        f"{API_URL}/v1/predict",
        json={"texts": texts},
        headers={"x-api-key": API_KEY},
        timeout=30,
    )
    latency_ms = (time.time() - start) * 1000
    response.raise_for_status()
    return latency_ms


if __name__ == "__main__":
    print("Starting load tests...")
    print(f"API URL: {API_URL}")
    print(f"Concurrent workers: {CONCURRENT_WORKERS}")

    # Check health first
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API health check failed")
            exit(1)
        print("✅ API is healthy")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        exit(1)

    # Run tests
    results = []
    results.append(("Single Prediction Load", single_prediction_load_test()))
    results.append(("Batch Prediction Load", batch_prediction_load_test()))
    results.append(("Sustained Load (60s)", sustained_load_test(60)))

    # Summary
    print("\n" + "=" * 80)
    print("LOAD TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(passed for _, passed in results)
    exit(0 if all_passed else 1)
