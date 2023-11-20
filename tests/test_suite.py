from running.config import Configuration
from running.runtime import DummyRuntime
from running.suite import BinaryBenchmarkSuite


def test_binary_benchmark_suite_quoted():
    b = BinaryBenchmarkSuite(
        name="foobar", programs={"ls": {"path": "/bin/ls", "args": 'foo "bar buzz"'}}
    )
    assert b.programs["ls"]["args"] == ["foo", "bar buzz"]


def test_dacapo_size():
    c = Configuration(
        {
            "suites": {
                "dacapo2006": {
                    "type": "DaCapo",
                    "release": "2006",
                    "path": "/usr/share/benchmarks/dacapo/dacapo-2006-10-MR2.jar",
                    "timing_iteration": 3,
                },
                "dacapo2006_default": {
                    "type": "DaCapo",
                    "release": "2006",
                    "path": "/usr/share/benchmarks/dacapo/dacapo-2006-10-MR2.jar",
                    "timing_iteration": 3,
                    "size": "default",
                },
            },
            "benchmarks": {
                "dacapo2006": [
                    "fop",
                    dict(name="fop_small", bm_name="fop", size="small"),
                ],
                "dacapo2006_default": ["fop"],
            },
        }
    )

    c.resolve_class()
    fop = c.get("benchmarks")["dacapo2006"][0]
    fop_default = c.get("benchmarks")["dacapo2006_default"][0]
    fop_small = c.get("benchmarks")["dacapo2006"][1]
    assert "-s" not in fop.to_string(DummyRuntime("java"))
    assert "-s default" in fop_default.to_string(DummyRuntime("java"))
    assert "-s small" in fop_small.to_string(DummyRuntime("java"))


def test_dacapo_timing_iteration():
    c = Configuration(
        {
            "suites": {
                "dacapo2006": {
                    "type": "DaCapo",
                    "release": "2006",
                    "path": "/usr/share/benchmarks/dacapo/dacapo-2006-10-MR2.jar",
                    "timing_iteration": 3,
                }
            },
            "benchmarks": {
                "dacapo2006": [
                    "fop",
                    dict(
                        name="fop_converge", bm_name="fop", timing_iteration="converge"
                    ),
                ]
            },
        }
    )

    c.resolve_class()
    fop = c.get("benchmarks")["dacapo2006"][0]
    fop_converge = c.get("benchmarks")["dacapo2006"][1]
    assert "-n 3" in fop.to_string(DummyRuntime("java"))
    assert "-converge" in fop_converge.to_string(DummyRuntime("java"))


def test_dacapo_path_ennvvar():
    c = Configuration(
        {
            "suites": {
                "dacapo2006_bogus": {
                    "type": "DaCapo",
                    "release": "2006",
                    # some bogus environment variable that will not be expanded
                    "path": "$DAHKDLHDIWHEIUWHEIWEHIJHDJKAGDKJADGUQDGIQUWDGI/dacapo-2006-10-MR2.jar",
                    "timing_iteration": 3,
                },
                "dacapo2006": {
                    "type": "DaCapo",
                    "release": "2006",
                    "path": "$HOME/dacapo-2006-10-MR2.jar",
                    "timing_iteration": 3,
                },
            }
        }
    )

    c.resolve_class()
    dacapo2006 = c.get("suites")["dacapo2006"]
    dacapo2006_bogus = c.get("suites")["dacapo2006_bogus"]
    assert "$HOME" not in str(dacapo2006.path)
    assert "$DAHKDLHDIWHEIUWHEIWEHIJHDJKAGDKJADGUQDGIQUWDGI" in str(
        dacapo2006_bogus.path
    )
