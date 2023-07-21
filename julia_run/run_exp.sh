LOG_DIR=0720_logs
INVOCATIONS=3

# 1.1x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 1 -i $INVOCATIONS
# 1.5x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 5 -i $INVOCATIONS
# 2x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 9 -i $INVOCATIONS
# 3x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 16 -i $INVOCATIONS
# 6x
running runbms ~/running-ng/$LOG_DIR julia_gcbench_bench.yml 32 32 -i $INVOCATIONS
# running runbms 0710_logs julia_gcbench_bench_stock.yml -i 1
