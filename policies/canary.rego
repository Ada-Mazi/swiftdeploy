package canary

default allow = false

allow {
    input.error_rate <= 0.01
    input.p99_latency_ms <= 500
}

deny_reasons[msg] {
    input.error_rate > 0.01
    msg = "Error rate exceeds 1%"
}

deny_reasons[msg] {
    input.p99_latency_ms > 500
    msg = "P99 latency exceeds 500ms"
}
