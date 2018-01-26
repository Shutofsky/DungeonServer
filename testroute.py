#!/usr/bin/python

routeFile = open("/proc/net/route",'r')

routeList = routeFile.read()

routeFile.close()

def hexStr_to_int(inputStr):
  hexDigits = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
  inputStr.upper()
  i = 0
  res = 0
  while i < len(inputStr):
    c = inputStr[i]
    if c not in hexDigits:
      return 0
    else:
      res += hexDigits.index(c)*pow(16, len(inputStr) - i - 1)
      i += 1
  return res

def getRouter():
  res = ''
  for routeLine in (routeList.split('\n')):
    dest = routeLine.split('\t')[1]
    gw = routeLine.split('\t')[2]
    if dest == '00000000':
      i = 0
      while i < 4:
        adrByte = ''
        adrByte += gw[(3-i)*2]
        adrByte += gw[(3-i)*2+1]
        res += str(hexStr_to_int(adrByte))
        if i < 3:
          res += '.'
        i += 1
      return res

print getRouter()


