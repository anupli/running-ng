LOG_DIR=0813_scan_stack_logs
INVOCATIONS=3

# 1.1x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 1 -i 3
# 1.5x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 5 -i 3
# 2x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 9 -i 3
# 3x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 16 -i 1
# 6x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 32 -i 1
# running runbms 0710_logs julia_gcbench_bench_stock.yml -i 1
