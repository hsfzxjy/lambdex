from lambdex import Def

def f():
    return Def.myfunc(lambda a, b: [  # comment1
        # comment2
        If[condition] [
            f2 < Def(lambda: [
                a+b
            ]),
            Return[f2],
        ],
        Try [  # comment3
            body,
        ].Except[Exception > e] [
            Excepthandler
        ],  # comment4
        # comment5
    ])