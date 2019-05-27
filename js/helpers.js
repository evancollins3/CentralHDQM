
const seriesColors = ["#7cb5ec", "#434348", "#90ed7d", "#f7a35c", "#8085e9", "#f15c80", "#e4d354", "#2b908f", "#f45b5b", "#91e8e1"]

function calculateRMS(yValues)
{
    // Concatenate all series
    var values = yValues.reduce((all, cur) => all.concat(cur), [])
    
    // Filter put all zeros
    values = values.filter(x => x != 0)

    var yValuesSum = values.reduce((total, num) => total + num, 0)
    var mean = yValuesSum / values.length

    var yValuesSquareSum = values.reduce((total, num) => total + (num * num), 0)
    var meanOfSquares = yValuesSquareSum / values.length

    var rms = Math.sqrt(meanOfSquares - (mean * mean))

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