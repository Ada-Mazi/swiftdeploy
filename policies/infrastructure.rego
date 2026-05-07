package infrastructure

default allow = false
default deny_reasons = []

allow {
    count(deny_reasons) == 0
}

deny_reasons[msg] {
    input.disk_free_gb < data.thresholds.min_disk_free_gb
    msg = sprintf("Disk free (%.1fGB) is below minimum (%.1fGB)", [input.disk_free_gb, data.thresholds.min_disk_free_gb])
}

deny_reasons[msg] {
    input.cpu_load > data.thresholds.max_cpu_load
    msg = sprintf("CPU load (%.2f) exceeds maximum (%.2f)", [input.cpu_load, data.thresholds.max_cpu_load])
}

deny_reasons[msg] {
    input.mem_free_percent < data.thresholds.min_mem_free_percent
    msg = sprintf("Memory free (%.1f%%) is below minimum (%.1f%%)", [input.mem_free_percent, data.thresholds.min_mem_free_percent])
}
