import marko

a = '[link](</my uri>)\n'

print(marko.Markdown()(a))
