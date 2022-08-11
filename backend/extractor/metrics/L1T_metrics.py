from basic import BaseMetric
import numpy as np
from linreg_AWB import linreg_eff
VERBOSE = False
#---- L1 Efficiency related
class EffMean(BaseMetric):
    def calculate(self, histo):
	from math import sqrt
    	mean = histo.GetSumOfWeights()/histo.GetEntries()
	err = mean / sqrt(histo.GetEntries())
	return (mean, err)

### to look deeper: GetMean(2) gives sumwy / sumw , with error of sqrt(sumwy2 / sumw - mean^2)
###                 each bin is fill with 1 entry? Or TEfficiency?
###		    need to know what is in sumwy
	

def EffMeanRange(histo, ibin_min, ibin_max):
    from math import sqrt
    total_entry = 0
    total_val   = 0
    for ibin in range(ibin_min, ibin_max+1):
	if histo.GetBi//nContent(ibin) == 0: continue   ## in Eff vs phi plot, the first bin and the last bin are empty
	bin_entry = (histo.GetBinContent(ibin) / histo.GetBinError(ibin)) ** 2.0 
	total_entry += bin_entry
        total_val   += bin_entry * histo.GetBinContent(ibin)
    if total_entry == 0 : return (0,0)
    mean     = total_val / total_entry
    stat_err = mean/sqrt(total_entry)
    if VERBOSE: print mean, stat_err
    return ( mean, stat_err )


def EffStdDev(histo, ibin_min, ibin_max):
    from math import sqrt
    total_entry   = 0
    total_val_sq  = 0
    #val_err_calc  = 0
    for ibin in range(ibin_min, ibin_max+1):
        if histo.GetBinContent(ibin) == 0: continue   ## in Eff vs phi plot, the first bin and the last bin are empty
	bin_entry = (histo.GetBinContent(ibin) / histo.GetBinError(ibin)) ** 2.0
	total_entry  += bin_entry
        total_val_sq += bin_entry * histo.GetBinContent(ibin) ** 2.0
	#val_err_calc += (bin_entry ** 2.0) * (histo.GetBinContent(ibin) ** 2.0) * (histo.GetBinError(ibin) ** 2.0)
    if total_entry == 0: return (0,0)
    mean, mean_err = EffMeanRange(histo, ibin_min, ibin_max)
    std = sqrt( total_val_sq / total_entry - mean ** 2.0)
    std_err = (mean * mean_err) / ( sqrt(ibin_max+1-ibin_min) * std)
    ## this is the err based on the approximation that the underlying distribution
    ## each bin is the same, and that we have used mean/sqrt(total+entry) as the mean_err
    ## the actual error propagation in as following

    ## std_err = sqrt(val_err_calc) / total_entry / std  
    ## simplified from the error propagation derived from the calculation of std
    ## larger than expected, need to understand the reason
    ## in the limit of infinite stats in each bin, std_err = mean_eff / sqrt(Nbins) ...
    if VERBOSE: print std_err
    return (std, std_err)



class EffMean(BaseMetric):
    def calculate(self, histo):
	if VERBOSE: print histo.GetSumOfWeights()
	if VERBOSE: print histo.GetEntries()
	if VERBOSE: print "running EffMeanTest \n\n"
	return EffMeanRange(histo, 1, histo.GetNbinsX())


class EffVariance(BaseMetric):
    def calculate(self, histo):
#	std, err = EffStdDev(histo, 1, histo.GetNbinsX())
#	print "MeanError(2)"
#	print histo.GetMeanError(2)
	return EffStdDev(histo, 1, histo.GetNbinsX())


#---- Efficiency Turn On related

# functions used by efficiency turn on calculations
def EffTurnOnPoint(eff, histo):
    point_bin = 0
    print '\n*** Inside EffTurnOnPoint for efficiency %.2f with %s***' % (eff, histo.GetName())
    xreg = []
    yreg = []
    yerr = []

    #yMin = histo.GetMinimum()
    #yMax = histo.GetMaximum()
    yMin = 0.0
    yMax = 1.0
    fMin = eff - 0.4*(eff - yMin)  ## For eff = 0.5, fMin = 0.3
    fMax = eff + 0.4*(yMax - eff)  ## For eff = 0.5, fMax = 0.7
    iMin = 1
    iMax = histo.GetNbinsX()
    if iMax - iMin < 3: return 0  ## Protect against accidentally running on low-bin plots
    for ibin in range(1, histo.GetNbinsX()):
        ibinerror = histo.GetBinError(ibin)
#        print 'ibincont is %f' % (histo.GetBinContent(ibin))
        if histo.GetBinContent(ibin) > (yMin + fMin*(yMax -yMin)) and histo.GetBinContent(ibin+1) > (yMin + fMin*(yMax-yMin)):
            # if histo.GetBinContent(ibin-1) <= (yMin + fMin*(yMax-yMin)):
            iMin = ibin
            break
    for ibin in range(1, histo.GetNbinsX()):
        # if histo.GetBinContent(ibin) < yMin + fMax*(yMax - yMin) and histo.GetBinContent(ibin+1) >= yMin + fMax*(yMax - yMin):
        #     if histo.GetBinContent(ibin-1) < yMin + fMax*(yMax - yMin):
        if histo.GetBinContent(ibin) >= yMin + fMax*(yMax - yMin) and histo.GetBinContent(ibin+1) >= yMin + fMax*(yMax - yMin):
            iMax = ibin-1
            break

    while iMax - iMin < 2:
        iMax += 1
        iMin -= 1
        if iMin < 1:
            iMin += 1
            iMax += 1
        if iMax > histo.GetNbinsX():
            iMin -= 1
            iMax -= 1
        print 'iMin_minus1Val is %f, iMaxplus1Val is %f' %(histo.GetBinContent(iMin-1),histo.GetBinContent(iMax+1))
    #print 'yMin is %f, yMax is %f' %(yMin,yMax)
   # print 'iMin is %f, iMax is %f' %(iMin,iMax)
   # print 'iMinCent is %f, iMaxCent is %f' %(histo.GetBinCenter(iMin),histo.GetBinCenter(iMax))
# print 'iMin_minus1Val is %f, iMaxplus1Val is %f' %(histo.GetBinContent(iMin-1),histo.GetBinContent(iMax+1))
#    print '30 percent is %f, 70 percent is %f' %(yMin +(fMin*(yMax - yMin)),yMin + fMax*(yMax - yMin))
    for ibin in range(iMin,iMax+1):
        ibincent = histo.GetBinCenter(ibin)
        xreg.append(ibincent)
        ibincontent = histo.GetBinContent(ibin)
        yreg.append(ibincontent)
        yerr.append(histo.GetBinError(ibin))

    ## Original central HDQM logic from 2018
    for ibin in range(1, histo.GetNbinsX()-1 ):
        if histo.GetBinContent(ibin) <= eff and histo.GetBinContent(ibin+1) > eff:
            point_bin = ibin
            print '  * Found bin %d (%.3f to %.3f)' % (point_bin, histo.GetBinLowEdge(ibin), histo.GetBinLowEdge(ibin+1))
            break    # to avoid empty bins in high pt region
    if VERBOSE: print point_bin

    [turn_on_point, turn_on_err] = linreg_eff(xreg, yreg, yerr, eff)
    ## Expand fit range if turn-on point is not inside [iMin, iMax] window
    iTry = 0
    while iTry < 3:
        iTry += 1
        if turn_on_point > histo.GetBinLowEdge(iMin) and turn_on_point < histo.GetBinLowEdge(iMax+1) and \
           turn_on_err < 0.5*(histo.GetBinLowEdge(iMax+1) - histo.GetBinLowEdge(iMin)):
            break
        if iMin <= 1 and iMax >= histo.GetNbinsX():
            break
        if iMin >= 2:
            iMin -= 1
            xreg.insert(0, histo.GetBinCenter(iMin))
            yreg.insert(0, histo.GetBinContent(iMin))
            yerr.insert(0, histo.GetBinError(iMin))
        if iMax < histo.GetNbinsX():
            iMax += 1
            xreg.append(histo.GetBinCenter(iMax))
            yreg.append(histo.GetBinContent(iMax))
            yerr.append(histo.GetBinError(iMax))
        [turn_on_point, turn_on_err] = linreg_eff(xreg, yreg, yerr, eff)

    print '\nturn_on_point = %.4f +/- %.4f' % (turn_on_point, turn_on_err)
    print '\nKEEP: %.4f,%.4f \n' % (turn_on_point, turn_on_err)
    if np.isnan(turn_on_point) == True:
        print 'DEF_Fail nan'
        print 'HOLD ', turn_on_point
        return False
    return point_bin



def GetYErr(ibin, histo): 
    from math import sqrt
    if histo.GetBinError(ibin) < histo.GetBinContent(ibin):
	return histo.GetBinError(ibin)
    else:
        if histo.GetBinContent(ibin) == 0.0: 
            return 0.
	if VERBOSE: print histo.GetEntries()
	return histo.GetBinContent(ibin) / sqrt(histo.GetBinContent(ibin) * histo.GetEntries() / (histo.GetNbinsX() * 2.0) )
	# simplified from binomial std from numer and denom 


def EffTurnOnEtAndErr(eff, ibin, histo):
    from math import sqrt
    print '\n*** Inside EffTurnOnEtAndErr for eff %.2f, ibin %d, in %s***' % (eff, ibin, histo.GetName())
    #log_text = '\n*** Inside EffTurnOnEtAndErr for eff %.2f, ibin %d, in %s***' % (eff, ibin, histo.GetName())
    if histo.GetBinContent(ibin) == 0.0 or histo.GetBinContent(ibin+1) == 0.0 : print 'bin: %f bin1: %f  zero' %(ibin,ibin+1)
#    if histo.GetBinContent(ibin) == 0.0 : print 'bin: ', ibin, 'is ZERO!!!!' 
#    if histo.GetBinContent(ibin+1) == 0.0 : print 'bin1: ', ibin+1, 'is ZERO!!!!' 
    weight_1   = (histo.GetBinContent(ibin+1) - eff) / (histo.GetBinContent(ibin+1) - histo.GetBinContent(ibin))
    weight_2   = (eff - histo.GetBinContent(ibin))   / (histo.GetBinContent(ibin+1) - histo.GetBinContent(ibin))
    slope_inv  = (histo.GetBinCenter(ibin+1) - histo.GetBinCenter(ibin)) / (histo.GetBinContent(ibin+1) - histo.GetBinContent(ibin))

    errX_1   = histo.GetBinWidth(ibin)   * sqrt(1.0/12)
    errX_2   = histo.GetBinWidth(ibin+1) * sqrt(1.0/12)
    errY_1   = GetYErr(ibin, histo)
    errY_2   = GetYErr(ibin+1, histo)

    #print '  * w1 = %f, w2 = %f, si = %f, eX1 = %f, eX2 = %f, eY1 = %f, eY2 = %f' % (weight_1, weight_2, slope_inv, errX_1, errX_2, errY_1, errY_2)
    if histo.GetBinContent(ibin) != 0.0 and  (errY_1 / histo.GetBinContent(ibin) > 0.2 or errY_2 / histo.GetBinContent(ibin+1) > 0.2):
        errY_1divhisto  = errY_1 / histo.GetBinContent(ibin)
        errY_2divhisto  = errY_2 / histo.GetBinContent(ibin+1)
        print 'bin: %f bin1: %f' % (ibin,ibin+1)
        if errY_1divhisto > 0.2: 
            #log_text += '\nerrY_1divhisto (= %f) is greater than 0.2' %(errY_1divhisto)
            print 'errY_1divhisto (= %f) is greater than 0.2' %(errY_1divhisto)
        if errY_2divhisto > 0.2:
            print 'errY_2divhisto (= %f) is greater than 0.2' %(errY_2divhisto)
#        print '****** errY_1divhisto =%f, errY_2divhisto = %f' % (errY_1divhisto, errY_2divhisto)            
#	return (0,0)

    eff_energy = weight_1 * histo.GetBinCenter(ibin) + weight_2 * histo.GetBinCenter(ibin+1)
    ibincenter = histo.GetBinCenter(ibin)
    ibinpluscenter = histo.GetBinCenter(ibin+1)
    ibincont= histo.GetBinContent(ibin)
    ibinpluscont = histo.GetBinContent(ibin+1)
 #   print 'ibin = %f, ibin+1 =%f' % (ibin, ibin+1)
  #  print 'ibin content = %f, bin content of ibin+1 = %f' % (ibincont, ibinpluscont)
   # print 'bin center of ibin = %f, bin center of ibin+1 = %f' % (ibincenter, ibinpluscenter)
    energy_err = sqrt( pow(weight_1 * errX_1, 2.0) + pow(weight_2 * errX_2, 2.0) + pow(slope_inv * weight_1 * errY_1, 2.0) + pow(slope_inv * weight_2 * errY_2, 2.0) )
    print 'HOLD %f,%f' % (eff_energy, energy_err)
    if histo.GetBinContent(ibin) != 0.0 and  (errY_1 / histo.GetBinContent(ibin) > 0.2 or errY_2 / histo.GetBinContent(ibin+1) > 0.2):
        print 'DEF_Fail %f,%f' % (eff_energy, energy_err)  
    else:
        print 'DEF_Fail GOOD' 
    print ' * Returning eff_energy = %f, energy_err = %f' % ( eff_energy, energy_err)
    print ' %.2f +/- %.2f' % (eff_energy, energy_err)
    if VERBOSE:
        return (round(eff_energy,2), round(energy_err,2))
# End of functions def



class TurnOnCurveEffPoint(BaseMetric):
    def __init__(self, eff_point):
	self.__eff_point = float(eff_point)
    
    def calculate(self, histo):
	if self.__eff_point < 0 or self.__eff_point > 1:  return (0, 0)
	ibin = EffTurnOnPoint(self.__eff_point, histo)
        if not ibin:
            return (0,0)
	if ibin == 0: return (0, 0)
	return EffTurnOnEtAndErr(self.__eff_point, ibin, histo)


class TurnOnCurveHalfWidth(BaseMetric):
    def calculate(self, histo):
	from math import sqrt
	ibin_20 = EffTurnOnPoint(0.2, histo)
	ibin_80 = EffTurnOnPoint(0.8, histo)
	if ibin_20 >= ibin_80 or ibin_20 == 0: return (0, 0)

	energy_20, err_20 = EffTurnOnEtAndErr(0.2, ibin_20, histo)
	energy_80, err_80 = EffTurnOnEtAndErr(0.8, ibin_80, histo)
	err_width = sqrt( err_20 **2.0 + err_80 **2.0 )
	if energy_20 == 0 or energy_80 == 0:
	    return (0, 0)
	return (energy_80 - energy_20, err_width)


class TurnOnCurveRange(BaseMetric):
    def calculate(self, histo):
	start_bin = 0
	saturate_bin = 0
	for ibin in range(1, histo.GetNbinsX()-1 ):
	    if histo.GetBinContent(ibin) == 0 and histo.GetBinContent(ibin+1) > 0:
		start_bin = ibin
		break
	for ibin in range(1, histo.GetNbinsX()-1 ):
            if histo.GetBinContent(ibin) != 0 and histo.GetBinContent(ibin) != 1.0:
		saturate_bin = ibin
	if saturate_bin == 0: return (0, 0)
	start_energy    = histo.GetBinCenter(start_bin)
	saturate_energy = histo.GetBinCenter(saturate_bin)

	if VERBOSE: print start_energy, saturate_energy
	return ( (saturate_energy + start_energy)/2.0, (saturate_energy - start_energy)/2.0 )



class TurnOnPlateauEff(BaseMetric):
    def calculate(self, histo):
	if VERBOSE: print "calculating plateau"
	TOEP = TurnOnCurveEffPoint(0.5)
	TOHW = TurnOnCurveHalfWidth()
	midpoint, mp_err = TOEP.calculate(histo)
	halfwidth, hw_err = TOHW.calculate(histo)

	if VERBOSE: print "got midpoint and halfwidth"
	if VERBOSE: print midpoint, halfwidth
	if midpoint == 0 or halfwidth == 0: return (0,0)
	plateau_val = midpoint + 2.0 * halfwidth
	plateau_bin = 0
	for ibin in range(1,histo.GetNbinsX()):
	    if histo.GetBinCenter(ibin) < plateau_val and histo.GetBinCenter(ibin+1) >= plateau_val:
		plateau_bin = ibin+1
		break
	if plateau_bin == 0: return (0,0)

	if VERBOSE: print "plateau_bin = %d" %plateau_bin
	if VERBOSE: print "eff and err are"
	if VERBOSE: print EffMeanRange(histo, plateau_bin, histo.GetNbinsX())
	return EffMeanRange(histo, plateau_bin, histo.GetNbinsX())

 

class TauSavePlots(BaseMetric):
   def calculate(self, histo):
	return (0, 0)

