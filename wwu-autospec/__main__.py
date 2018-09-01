import os
import platform
import sys

opsys=platform.system()
if opsys=='Darwin': opsys='Mac' #For some reason Macs identify themselves as Darwin. I don't know why but I think this is more intuitive.

package_loc=''

if opsys=='Windows':
    rel_package_loc='\\'.join(__file__.split('\\')[:-1])+'\\'
    if 'C:' in rel_package_loc:
        package_loc=rel_package_loc
    else: package_loc=os.getcwd()+'\\'+rel_package_loc
    print(package_loc)

elif opsys=='Linux':
    rel_package_loc='/'.join(__file__.split('/')[:-1])+'/'
    if rel_package_loc[0]=='/':
        package_loc=rel_package_loc
    else: package_loc=os.getcwd()+'/'+rel_package_loc
else:
    print("AHH I'm on a Mac!!")
    exit()
    
sys.path.append(package_loc)

import controller
controller.main()