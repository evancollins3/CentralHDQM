
const seriesColors = ["#7cb5ec", "#434348", "#90ed7d", "#f7a35c", "#8085e9", "#f15c80", "#e4d354", "#2b908f", "#f45b5b", "#91e8e1"]

function calculateMeanAndRMS(yValues)
{
    // Concatenate all series
    var values = yValues.reduce((all, cur) => all.concat(cur), [])

    // Filter out all zeros
    values = values.filter(x => x != 0)

    var yValuesSum = values.reduce((total, num) => total + num, 0)
    var mean = yValuesSum / values.length

    var yValuesSquareSum = values.reduce((total, num) => total + (num * num), 0)
    var meanOfSquares = yValuesSquareSum / values.length

    var rms = Math.sqrt(meanOfSquares - (mean * mean))

    return [mean, rms]
}

function getYRange(mean, rms)
{
    var min_y = mean - (5 * rms)
    var max_y = mean + (5 * rms)

    return [min_y, max_y]
}

function safeGetAtIndex(array, index)
{
    if(array != undefined)
        return array[index]
    else
    {
        return undefined
    }
}

function linearRegression(data) 
{
    var avg_y = 0, avg_x = 0
    var start_x = Infinity, end_x = 0
    var start_y = Infinity, end_y = 0

    for (var i = 0; i < data.length; i++) 
    {
        avg_y += data[i].y
        avg_x += data[i].x
        if (start_x > data[i].x)
            start_x = data[i].x
        if (end_x < data[i].x) 
            end_x = data[i].x
        if (start_y > data[i].y)
            start_y = data[i].y
        if (end_y < data[i].y) 
            end_y = data[i].y
    }

    start_x -= Math.abs(start_x)
    end_x += Math.abs(end_x)
    start_y -= Math.abs(start_y)
    end_y += Math.abs(end_y)
    avg_x /= data.length
    avg_y /= data.length

    var cov_xy = 0
    var var_x = 0
    var var_y = 0

    for (var i = 0; i < data.length; i++) 
    {
        cov_xy += (data[i].x - avg_x) * (data[i].y - avg_y)
        var_x += Math.pow(data[i].x - avg_x, 2)
        var_y += Math.pow(data[i].y - avg_y, 2)
    }

    var a_x = cov_xy / var_x
    var b_x = avg_y - a_x * avg_x
    var res = [[start_x, a_x * start_x + b_x], [end_x, a_x * end_x + b_x]]
    
    return res;
}

// Returns a color based on val which must be between 0.0 and 1.0
function colorScale(val) 
{
    var r, g, b = 0
    var perc = 100 - val * 100

    if(perc < 50) 
    {
		r = 255;
		g = Math.round(5.1 * perc)
	}
    else 
    {
		g = 255
		r = Math.round(510 - 5.10 * perc)
    }
    
	var h = r * 0x10000 + g * 0x100 + b * 0x1
	return '#' + ('000000' + h.toString(16)).slice(-6)
}

function getSeriesTitleByFilename(fileName) 
{
    if(fileName.indexOf("perInOutLayer") !== -1) 
    {   
        //Convention: for plus or minus trends only, the first trend must be disk -/+3 and is called "perMinusDisk" or "perPlusDisk" in the title. So the title is correct and the legend also
        fileName = 'Inner Layer 1'
    }

    for(var number = 1; number <= 4; number++) 
    {
        //If we have several plots on the same plot, show the layer number instead...  
        if ((fileName.indexOf("Module" + number) !== -1)) 
        {
            fileName = 'Module ' + number
            continue
        }
    }

    for(var number = 1; number <= 2; number++)
    {
        //If we have several plots on the same plot, show the layer number instead...  
        if (((fileName.indexOf("Ring" + number) !== -1) || (fileName.indexOf("R" + number) !== -1)) && (fileName.indexOf("TEC") == -1) && (fileName.indexOf("TID") == -1)) 
        {
            fileName = 'Ring ' + number
            continue
        }
    }

    for(var number = 1; number <= 6; number++)
    {
        //If we have several plots on the same plot, show the layer number instead...
        if((fileName.indexOf("InnerLayer" + number) !== -1) || (fileName.indexOf("TIB_L" + number) !== -1)) 
        {
            fileName = 'Inner Layer ' + number
            continue
        }
        if((fileName.indexOf("OuterLayer" + number) !== -1) || (fileName.indexOf("TOB_L" + number) !== -1))
        {
            fileName = 'Outer Layer ' + number
            continue
        }
        if((fileName.indexOf("Layer" + number) !== -1) || (fileName.indexOf("L" + number) !== -1))
        {
            fileName = 'Layer ' + number
            continue
        }
    }

    for(var number = 1; number <= 7; number++)
    {
        //If we have several plots on the same plot, show the layer number instead...
        if((fileName.indexOf("TEC_MINUS_R" + number) !== -1)) 
        {
            fileName = 'TEC- R ' + number
            continue
        }
        if((fileName.indexOf("TEC_PLUS_R" + number) !== -1))
        {
            fileName = 'TEC+ R ' + number
            continue
        }
    }

    for(var number = 1; number <= 9; number++)
    {
        //If we have several plots on the same plot, show the layer number instead...
        if((fileName.indexOf("TEC_MINUS_W" + number) !== -1))
        {
            fileName = 'TEC- W ' + number
            continue
        }
    }

    for(var number = 1; number <= 9; number++)
    { 
        //If we have several plots on the same plot, show the layer number instead...
        if((fileName.indexOf("TEC_PLUS_W" + number) !== -1)) 
        {
            fileName = 'TEC+ W ' + number
            continue
        }
    }

    for(var number = 1; number <= 3; number++)
    {
        //or the disk number
        if(fileName.indexOf("Dm" + number) !== -1)
        {
            fileName = 'Disk -' + number
            continue
        }

        if(fileName.indexOf("Dp" + number) !== -1)
        {
            fileName = 'Disk +' + number
            continue
        }

        if(fileName.indexOf("TID_PLUS_R" + number) !== -1)
        {
            fileName = 'TID+ R' + number
            continue
        }

        if(fileName.indexOf("TID_MINUS_R" + number) !== -1)
        {
            fileName = 'TID- R' + number
            continue
        }

        if(fileName.indexOf("TID_PLUS_W" + number) !== -1)
        {
            fileName = 'TID+ W' + number
            continue
        }

        if(fileName.indexOf("TID_MINUS_W" + number) !== -1)
        {
            fileName = 'TID- W' + number
            continue
        }
    }
    if(fileName.indexOf("perLayer") !== -1)
    {
        //Convention: the first trend must be layer 1 and is called "perLayer" in the title. So the title is correct and the legend also
        fileName = 'Layer 1'
    }
    if((fileName.indexOf("perDisk") !== -1) || (fileName.indexOf("perMinusDisk") !== -1))
    {
        //Convention: the first trend must be disk -3 and is called "perDisk" in the title. So the title is correct and the legend also
        fileName = 'Disk -3'
    }
    if(fileName.indexOf("perPlusDisk") !== -1)
    {
        //Convention: for plus or minus trends only, the first trend must be disk -/+3 and is called "perMinusDisk" or "perPlusDisk" in the title. So the title is correct and the legend also
        fileName = 'Disk +3'
    }

    return fileName
}