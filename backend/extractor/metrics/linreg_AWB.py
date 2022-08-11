
import numpy as np
from linfit import linfit


def linreg_eff(xVal, yVal, yErr, eff):

    x = np.array(xVal)
    y = np.array(yVal)
    yE = np.array(yErr)

    fit, cvm, info = linfit(x, y, sigmay=yE, relsigma=False, return_all=True)
    dfit = [np.sqrt(cvm[i,i]) for i in range(2)]

    turnon_point = (eff -fit[1])/fit[0]
    #variance in turn on point
    varitp = ((eff - fit[1])**2)/(fit[0]**4)*cvm[0][0]+2*(eff - fit[1])/(fit[0]**3)*cvm[0][1]+(fit[0])**(-2)*cvm[1][1]
    uncertp = np.sqrt(varitp)
    print '%d percent turn on point from fit is %f +/- %f' %(eff*100, turnon_point, uncertp)

    return [turnon_point, uncertp]
