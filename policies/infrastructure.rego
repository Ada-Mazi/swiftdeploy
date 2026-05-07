package infrastructure

import future.keywords.if

default allow := false

allow if {
    input.disk_free_gb >= 8.0
    input.cpu_load <= 2.0
    input.mem_free_percent >= 10.0
}
