from lambdex import def_

def f():
    return def_.myfunc(  # comment1
        lambda a, b:   [# comment2
  if_[condition] [
      f2 < def_(lambda:[a+b]),
      return_[f2],
            ].else_[c],try_[# comment3
      body,
  ].except_[Exception > e] [
      except_handler
  ] # comment4
  ,         ],# comment5
        )