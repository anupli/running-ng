from pathlib import Path
from running.config import Configuration
from running.util import (
    parse_config_str,
    smart_quote,
    split_quoted,
    detect_rogue_processes,
)


def test_split_quoted():
    assert split_quoted('123 "foo bar"') == ["123", "foo bar"]


def test_smart_quote():
    assert smart_quote(Path("/bin") / "123 456") == '"/bin/123 456"'


def test_issue104():
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
            "benchmarks": {"dacapo2006": ["fop"]},
            "runtimes": {
                "jdk8": {
                    "type": "OpenJDK",
                    "release": 8,
                    "home": "/usr/lib/jvm/temurin-8-jdk-amd64",
                }
            },
            "modifiers": {},
        }
    )
    c.resolve_class()
    _, modifiers = parse_config_str(c, "jdk8|")
    assert len(modifiers) == 0


def test_detect_rogue_processes():
    # Test with no rogue processes
    top_output_normal = """top - 03:18:43 up 4 min,  1 user,  load average: 0.55, 0.35, 0.15
Tasks: 181 total,   1 running, 180 sleeping,   0 stopped,   0 zombie
%Cpu(s):  0.0 us,  2.2 sy,  0.0 ni, 97.8 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st 
MiB Mem :  15995.6 total,  13333.4 free,   1396.1 used,   1616.3 buff/cache     
MiB Swap:   4096.0 total,   4096.0 free,      0.0 used.  14599.5 avail Mem 

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
   3524 runner    20   0   12340   5384   3336 R  10.0   0.0   0:00.01 top -bcn 1 -w512
      1 root      20   0   22876  13828   9476 S   0.0   0.1   0:03.23 /sbin/init"""

    rogue_processes = detect_rogue_processes(top_output_normal)
    assert len(rogue_processes) == 0

    # Test with one rogue process
    top_output_rogue = """top - 03:18:43 up 4 min,  1 user,  load average: 0.55, 0.35, 0.15
Tasks: 181 total,   1 running, 180 sleeping,   0 stopped,   0 zombie
%Cpu(s):  0.0 us,  2.2 sy,  0.0 ni, 97.8 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st 
MiB Mem :  15995.6 total,  13333.4 free,   1396.1 used,   1616.3 buff/cache     
MiB Swap:   4096.0 total,   4096.0 free,      0.0 used.  14599.5 avail Mem 

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
   1234 user      20   0  123456   7890   4567 S  85.3   0.1   0:12.34 rust-analyzer
   3524 runner    20   0   12340   5384   3336 R  10.0   0.0   0:00.01 top -bcn 1 -w512
      1 root      20   0   22876  13828   9476 S   0.0   0.1   0:03.23 /sbin/init"""

    rogue_processes = detect_rogue_processes(top_output_rogue)
    assert len(rogue_processes) == 1
    pid, user, cpu_percent, command = rogue_processes[0]
    assert pid == "1234"
    assert user == "user"
    assert cpu_percent == 85.3
    assert command == "rust-analyzer"

    # Test with custom threshold
    rogue_processes_low_threshold = detect_rogue_processes(
        top_output_rogue, cpu_threshold=5.0
    )
    assert (
        len(rogue_processes_low_threshold) == 2
    )  # Both rust-analyzer (85.3%) and top (10.0%)

    # Test with high threshold
    rogue_processes_high_threshold = detect_rogue_processes(
        top_output_rogue, cpu_threshold=90.0
    )
    assert len(rogue_processes_high_threshold) == 0  # No processes above 90%


def test_detect_rogue_processes_malformed():
    # Test with malformed top output (no header)
    malformed_output = """some random text
not a top output
no PID header"""

    rogue_processes = detect_rogue_processes(malformed_output)
    assert len(rogue_processes) == 0

    # Test with empty output
    rogue_processes = detect_rogue_processes("")
    assert len(rogue_processes) == 0
