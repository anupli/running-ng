from running.benchmark import JavaBenchmark
from running.modifier import *
from running.config import Configuration


def test_jvm_arg():
    j = JVMArg(name="j", val="-Xms100M -D\"foo bar\"")
    assert j.val == ["-Xms100M", "-Dfoo bar"]


def test_jvm_classpath():
    j = JVMClasspath(name="j", val="/bin /foo \"/Users/John Citizen/\"")
    assert j.val == ["/bin", "/foo", "/Users/John Citizen/"]

    jb = JavaBenchmark(
        jvm_args=[], program_args=[], cp=["fizzbuzz"],
        suite_name="dacapo", name="fop"
    )
    jb = jb.attach_modifiers([j])
    assert jb.cp == ["fizzbuzz", "/bin", "/foo", "/Users/John Citizen/"]


def test_jvm_classpath_append():
    j = JVMClasspathAppend(name="j", val="/bin /foo \"/Users/John Citizen/\"")
    assert j.val == ["/bin", "/foo", "/Users/John Citizen/"]

    jb = JavaBenchmark(
        jvm_args=[], program_args=[], cp=["fizzbuzz"],
        suite_name="dacapo", name="fop"
    )
    jb = jb.attach_modifiers([j])
    assert jb.cp == ["fizzbuzz", "/bin", "/foo", "/Users/John Citizen/"]


def test_jvm_classpath_prepend():
    j = JVMClasspathPrepend(name="j", val="/bin /foo \"/Users/John Citizen/\"")
    assert j.val == ["/bin", "/foo", "/Users/John Citizen/"]

    jb = JavaBenchmark(
        jvm_args=[], program_args=[], cp=["fizzbuzz"],
        suite_name="dacapo", name="fop"
    )
    jb = jb.attach_modifiers([j])
    assert jb.cp == ["/bin", "/foo", "/Users/John Citizen/", "fizzbuzz"]


def test_program_arg():
    p = ProgramArg(name="p", val="/bin /foo \"/Users/John Citizen/\"")
    assert p.val == ["/bin", "/foo", "/Users/John Citizen/"]


def test_expand_value_opts():
    p = EnvVar(name="path", var="PATH", val="{0}:{1}")
    assert p.val == "{0}:{1}"
    p = p.apply_value_opts(value_opts=["/bin", "/sbin"])
    assert p.val == "/bin:/sbin"


def test_modifier_set():
    c = Configuration({
        "modifiers": {
            "a": {
                "type": "JVMArg",
                "val": "-XX:GC={0}"
            },
            "b": {
                "type": "EnvVar",
                "var": "FOO",
                "val": "BAR"
            },
            "c": {
                "type": "EnvVar",
                "var": "FIZZ",
                "val": "BUZZ"
            },
            "set": {
                "type": "ModifierSet",
                "val": "a-{0}|b"
            },
            "set_nested": {
                "type": "ModifierSet",
                "val": "set-{0}|c"
            }
        }
    })
    c.resolve_class()
    mods = c.get("modifiers")["set"].apply_value_opts(
        value_opts=["NoGC"]).flatten(c)
    mods = c.get("modifiers")["set_nested"].apply_value_opts(
        value_opts=["NoGC"]).flatten(c)
    assert len(mods) == 3
