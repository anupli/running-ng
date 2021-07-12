from running.modifier import JVMArg, JVMClasspath, ProgramArg, EnvVar


def test_jvm_arg():
    j = JVMArg(name="j", val="-Xms100M -D\"foo bar\"")
    assert j.val == ["-Xms100M", "-Dfoo bar"]


def test_jvm_classpath():
    j = JVMClasspath(name="j", val="/bin /foo \"/Users/John Citizen/\"")
    assert j.val == ["/bin", "/foo", "/Users/John Citizen/"]


def test_program_arg():
    p = ProgramArg(name="p", val="/bin /foo \"/Users/John Citizen/\"")
    assert p.val == ["/bin", "/foo", "/Users/John Citizen/"]


def test_expand_value_opts():
    p = EnvVar(name="path", var="PATH", val="{0}:{1}")
    assert p.val == "{0}:{1}"
    p = p.apply_value_opts(value_opts=["/bin", "/sbin"])
    assert p.val == "/bin:/sbin"
