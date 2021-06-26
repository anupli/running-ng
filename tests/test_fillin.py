from running.command.fillin import fillin


def test_fillin():
    results = []
    fillin(lambda base, ns: results.append(list(ns)), 3)
    assert results == [[0, 4, 8], [2, 6], [1, 3, 5, 7]]

    results = []
    fillin(lambda base, ns: results.append(list(ns)), 4)
    assert results == [
        [0, 8, 16],
        [4, 12],
        [2, 6, 10, 14],
        [1, 3, 5, 7, 9, 11, 13, 15]
    ]


def test_fillin_start():
    results = []
    fillin(lambda base, ns: results.append(list(ns)), 3, 1)
    assert results == [[1, 3, 5, 7]]

    results = []
    fillin(lambda base, ns: results.append(list(ns)), 4, 2)
    assert results == [[2, 6, 10, 14], [1, 3, 5, 7, 9, 11, 13, 15]]
