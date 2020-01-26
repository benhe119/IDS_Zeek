f = open("Injection_template.txt", "r")
f = f.read()

print(f.count("var_txt"))
print(f.format(txt_1="a",txt_2="b",txt_3="c",txt_4="d"))

import re
x1 = "no_of_goose <=1 && breaker_status==true && stNum < prev_stNum && sqNum == 0+|+is_busy==false"
x1 = x1.strip()
x1 = x1.replace(" ", "")
print(re.sub('<(?!=)', ' >= ', x1))
print(re.split('<(?!=)|<=|==|=(?!=)|>(?!=)|>=', x1))
#print(re.sub('<(?=)', ' > ', x1))

import re

str = "The rain in Spain falls mainly in the plain!"

#Check if the string contains either "falls" or "stays":

x = re.findall("falls?!hshs", str)

function_format = "function {a} ({b}): {c}\n{{\n{d}\n}}".format(a=1, b=2, c=3, d=4)
print(function_format)

print(x)

if (x):
  print("Yes, there is at least one match!")
else:
  print("No match")

x2 = ['breaker_status==true', 'meas_net_current==0', 'breaker_status == false', 'GOOSE!', 'no_of_goose=1,breaker_status = true, stNum=stNum+1, sqNum=0', 'meas_net_current > threshold_of_relay', 'SV?', 'is_busy==true', 'GOOSE?', 'is_busy=true', 'no_of_goose==10', 'no_of_goose<=1 && breaker_status ==true && stNum < prev_stNum && sqNum !=0', 'no_of_goose <=1 && breaker_status==true && stNum > prev_stNum && sqNum ==0', 'trip_signal!', 'prev_stNum = stNum', 'is_busy==false', 'GOOSE?', 'wait<=3', 'trip_signal?', 'wait=0', 'wait>=3', 'breaker_status=false', 'manual reset', 'timer<=1', 'timer>=1', 'SV!', 'timer=0,\nupdateNetCurrent(),\nno_of_SV++', 'SV!', 'timer=0,\ninitMU()', 'atktimer<=1', 'atktimer>=1', 'GOOSE!', 'atktimer=0,\nno_of_goose=10', 'no_of_SV==5', 'GOOSE!', 'breaker_status=true,stNum=prev_stNum+1,sqNum=0']
x3 = []
for x in x2:
  y = re.findall("[>=<+-]",x)
  if len(y) != 0:
    x3.append(x)
print(x3)
