package infrastructure

import future.keywords.if
import future.keywords.in

default allow = false
default deny_reasons = []

allow if {
    count(deny_reasons) == 0
}

deny_reasons contains msg if {
    input.disk_free_gb < data.thresholds.min_disk_free_gb
    msg := sprintf("Disk free (%.1fGB) is below minimum (%.1fGB)", [input.disk_free_gb, data.thresholds.min_disk_free_gb])
}

deny_reasons contains msg if {
    input.cpu_load > data.thresholds.max_cpu_load
    msg := sprintf("CPU load (%.2f) exceeds maximum (%.2f)", [input.cpu_load, data.thresholds.max_cpu_load])
}

deny_reasons contains msg if {
    input.mem_free_percent < data.thresholds.min_mem_free_percent
    msg := sprintf("Memory free (%.1f%%) is below minimum (%.1f%%)", [input.mem_free_percent, data.thresholds.min_mem_free_percent])
}
