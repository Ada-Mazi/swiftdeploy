package canary

default allow = false
default deny_reasons = []

allow {
    count(deny_reasons) == 0
}

deny_reasons[msg] {
    input.error_rate > data.thresholds.max_error_rate
    msg = sprintf("Error rate (%.2f%%) exceeds maximum (%.2f%%)", [input.error_rate * 100, data.thresholds.max_error_rate * 100])
}

deny_reasons[msg] {
    input.p99_latency_ms > data.thresholds.max_p99_latency_ms
    msg = sprintf("P99 latency (%dms) exceeds maximum (%dms)", [input.p99_latency_ms, data.thresholds.max_p99_latency_ms])
}
