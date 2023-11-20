from running.config import Configuration


def test_openjdk_path_ennvvar():
    c = Configuration(
        {
            "runtimes": {
                "temurin-21_bogus": {
                    "type": "OpenJDK",
                    "release": 21,
                    # some bogus environment variable that will not be expanded
                    "home": "$DAHKDLHDIWHEIUWHEIWEHIJHDJKAGDKJADGUQDGIQUWDGI/temurin-21-jdk-amd64",
                },
                "temurin-21": {
                    "type": "OpenJDK",
                    "release": 21,
                    "home": "$HOME/temurin-21-jdk-amd64",
                },
            }
        }
    )

    c.resolve_class()
    temurin_21_bogus = c.get("runtimes")["temurin-21_bogus"]
    temurin_21 = c.get("runtimes")["temurin-21_bogus"]
    assert "$HOME" not in str(temurin_21.home)
    assert "$DAHKDLHDIWHEIUWHEIWEHIJHDJKAGDKJADGUQDGIQUWDGI" in str(
        temurin_21_bogus.home
    )
