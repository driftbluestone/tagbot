import sys, json
args = sys.argv
args.extend(["1", "2", "3", "dn"])
if len(args) == 4:
  print("No input to convert to int")
  sys.exit()
args = args[4]
args = args.encode()
num = 0
for i in args:
  num += i
print("{" + f"\"{args.decode()}\":" + f"{num}" + "}")