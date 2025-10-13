# Performance Benchmarks

This document outlines the performance benchmarks for the `async-mariadb-connector` library, comparing asynchronous operations against their synchronous counterparts.

## Environment

-   **CPU:** AMD Ryzen 7 5825U
-   **RAM:** 16GB
-   **MariaDB Version:** 11.8.3
-   **Python Version:** 3.11.3
-   **`aiomysql` Version:** 0.2.0
-   **`PyMySQL` Version:** [Version, e.g., 1.1.0]

## Benchmark: Bulk Inserts

This test measures the time taken to insert a large number of records into the database.

### Results

| Operation             | Records | Time Taken (seconds) |
| --------------------- | ------- | -------------------- |
| **Async Bulk Insert** | 10,000  | 0.1967               |
| Sync Bulk Insert      | 10,000  | 0.2048               |

*Lower is better.*

### Analysis

The asynchronous bulk insert is slightly faster, but the main advantage of async is not always raw speed for a single operation, but its ability to handle concurrent operations without blocking.

## Benchmark: Concurrent Reads

This test simulates a high-concurrency scenario where multiple clients are reading data from the database simultaneously.

### Results

| Operation           | Concurrent Tasks | Total Queries | Time Taken (seconds) |
| ------------------- | ---------------- | ------------- | -------------------- |
| **Async Concurrent Reads** | 100              | 10,000        | 0.0661               |
| Sync Concurrent Reads | 100              | 10,000        | 0.0927               |

*Lower is better.*

### Conclusion

The benchmarks clearly demonstrate the performance advantage of using the asynchronous connector.

-   **Bulk Insert:** The async connector shows a modest improvement.
-   **Concurrent Reads:** The async connector is significantly faster, completing the tasks in roughly 71% of the time it took the synchronous method. This highlights the power of `asyncio` for I/O-bound workloads, as it can handle many database operations concurrently without waiting for each one to complete.
