from running.command.log_preprocessor import filter_stats, reduce_stats, sum_work_perf_event, calc_work_ipc, ratio_work_perf_event


def test_filter():
    assert filter_stats(lambda x: "foo" in x)({
        "foo1": 1,
        "2foo": 2,
        "bar3": 3,
        "4bar": 4
    }) == {"foo1": 1, "2foo": 2}


def test_reduce():
    assert reduce_stats(r"\d*foo\d*", "foo_sum", lambda x, y: x + y)({
        "foo1": 1,
        "2foo": 2,
        "bar3": 3,
        "4bar": 4
    })["foo_sum"] == 3


def test_sum_perf():
    assert sum_work_perf_event("PERF_COUNT_HW_CPU_CYCLES")({
        "work.ScanUniverseRoots.PERF_COUNT_HW_CPU_CYCLES.total": 1,
        "work.PrepareCollector.PERF_COUNT_HW_CPU_CYCLES.total": 2,
        "work.ScanUniverseRoots.PERF_COUNT_HW_CACHE_L1D:MISS.total": 3
    })["work.PERF_COUNT_HW_CPU_CYCLES.total"] == 3


def test_ratio_perf():
    stats = {
        "work.ScanUniverseRoots.PERF_COUNT_HW_CPU_CYCLES.total": 2,
        "work.PrepareCollector.PERF_COUNT_HW_CPU_CYCLES.total": 3,
        "work.foo.PERF_COUNT_HW_CPU_CYCLES.total": 5
    }
    stats = sum_work_perf_event("PERF_COUNT_HW_CPU_CYCLES")(stats)
    ratios = ratio_work_perf_event("PERF_COUNT_HW_CPU_CYCLES")(stats)
    assert ratios["work.ScanUniverseRoots.PERF_COUNT_HW_CPU_CYCLES.ratio"] == 0.2
    assert ratios["work.PrepareCollector.PERF_COUNT_HW_CPU_CYCLES.ratio"] == 0.3
    assert ratios["work.foo.PERF_COUNT_HW_CPU_CYCLES.ratio"] == 0.5


def test_ipc():
    ipcs = calc_work_ipc({
        "work.foo.PERF_COUNT_HW_CPU_CYCLES.total": 20,
        "work.foo.PERF_COUNT_HW_INSTRUCTIONS.total": 4,
        "work.bar.PERF_COUNT_HW_CPU_CYCLES.total": 10,
        "work.bar.PERF_COUNT_HW_INSTRUCTIONS.total": 5,
    })
    print(ipcs)
    assert ipcs["work.foo.INSTRUCTIONS_PER_CYCLE.ratio"] == 0.2
    assert ipcs["work.bar.INSTRUCTIONS_PER_CYCLE.ratio"] == 0.5
