from running.config import Configuration
from running.runtime import DummyRuntime
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


def test_dacapo_size():
    c = Configuration({
        "suites": {
            "dacapo2006": {
                "type": "DaCapo",
                "release": "2006",
                "path": "/usr/share/benchmarks/dacapo/dacapo-2006-10-MR2.jar",
                "timing_iteration": 3
            },
            "dacapo2006_default": {
                "type": "DaCapo",
                "release": "2006",
                "path": "/usr/share/benchmarks/dacapo/dacapo-2006-10-MR2.jar",
                "timing_iteration": 3,
                "size": "default"
            }
        },
        "benchmarks": {
            "dacapo2006": [
                "fop",
                dict(name="fop_small", bm_name="fop", size="small")
            ],
            "dacapo2006_default": [
                "fop"
            ]
        }
    })

    c.resolve_class()
    fop = c.get("benchmarks")["dacapo2006"][0]
    fop_default = c.get("benchmarks")["dacapo2006_default"][0]
    fop_small = c.get("benchmarks")["dacapo2006"][1]
    assert "-s" not in fop.to_string(DummyRuntime("java"))
    assert "-s default" in fop_default.to_string(DummyRuntime("java"))
    assert "-s small" in fop_small.to_string(DummyRuntime("java"))


def test_dacapo_timing_iteration():
    c = Configuration({
        "suites": {
            "dacapo2006": {
                "type": "DaCapo",
                "release": "2006",
                "path": "/usr/share/benchmarks/dacapo/dacapo-2006-10-MR2.jar",
                "timing_iteration": 3
            }
        },
        "benchmarks": {
            "dacapo2006": [
                "fop",
                dict(name="fop_converge", bm_name="fop",
                     timing_iteration="converge")
            ]
        }
    })

    c.resolve_class()
    fop = c.get("benchmarks")["dacapo2006"][0]
    fop_converge = c.get("benchmarks")["dacapo2006"][1]
    assert "-n 3" in fop.to_string(DummyRuntime("java"))
    assert "-converge" in fop_converge.to_string(DummyRuntime("java"))


def test_dacapo_openjdk_9_workaround():
    c = Configuration({
        "suites": {
            "dacapo2006": {
                "type": "DaCapo",
                "release": "2006",
                "path": "/usr/share/benchmarks/dacapo/dacapo-2006-10-MR2.jar",
                "timing_iteration": 3
            }
        },
        "benchmarks": {
            "dacapo2006": [
                "fop"
            ]
        },
        "runtimes": {
            "jdk8": {
                "type": "OpenJDK",
                "release": 8,
                "home": "/usr/lib/jvm/temurin-8-jdk-amd64"
            },
            "jdk11": {
                "type": "OpenJDK",
                "release": 11,
                "home": "/usr/lib/jvm/temurin-11-jdk-amd64"
            },
        },
        "configs": [
            "jdk8",
            "jdk11"
        ]
    })
    c.resolve_class()
    from running.benchmark import JavaBenchmark
    fop: JavaBenchmark
    fop = c.get("benchmarks")["dacapo2006"][0]
    jdk8 = c.get("runtimes")["jdk8"]
    jdk11 = c.get("runtimes")["jdk11"]
    fop_jdk8 = fop.attach_modifiers(fop.get_runtime_specific_modifiers(jdk8))
    fop_jdk11 = fop.attach_modifiers(fop.get_runtime_specific_modifiers(jdk11))
    print(fop_jdk8.to_string(jdk8))
    print(fop_jdk11.to_string(jdk11))
    assert "add-exports" not in fop_jdk8.to_string(jdk8)
    assert "add-exports" in fop_jdk11.to_string(jdk11)
