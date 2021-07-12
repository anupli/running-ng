from running.suite import BinaryBenchmarkSuite


def test_binary_benchmark_suite_quoted():
    b = BinaryBenchmarkSuite(
        name="foobar",
        programs={
            "ls": {
                "path": "/bin/ls",
                "args": "foo \"bar buzz\""
            }
        }
    )
    assert b.programs["ls"]["args"] == ["foo", "bar buzz"]
