package infrastructure

default allow = false

allow {
    input.disk_free_gb >= 8.0
    input.cpu_load <= 2.0
    input.mem_free_percent >= 10.0
}

deny_reasons[msg] {
    input.disk_free_gb < 8.0
    msg = "Disk free is below minimum (8.0GB)"
}

deny_reasons[msg] {
    input.cpu_load > 2.0
    msg = "CPU load exceeds maximum (2.0)"
}

deny_reasons[msg] {
    input.mem_free_percent < 10.0
    msg = "Memory free is below minimum (10%)"
}
