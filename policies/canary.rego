package canary

import future.keywords.if

default allow := false

allow if {
    input.error_rate <= 0.01
    input.p99_latency_ms <= 500
}
