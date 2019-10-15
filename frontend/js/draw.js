
async function draw(collection, data, renderTo, filterFunction = undefined) 
{
    if(filterFunction == undefined)
    {
        filterFunction = getFilteredArray
    }

    var filteredData = []
    var seriesTitles = []
    var yValues = []
    var yErr = []

    for(var i = 0; i < data.length; i++)
    {
        if(collection["files"].length == 1)
            seriesTitles[i] = collection["files"][i]
        else
            seriesTitles[i] = getSeriesTitleByFilename(collection["files"][i])

        filteredData[i] = await filterFunction(data[i])

        yValues[i] = filteredData[i].map(x => x.y)
        yErr[i] = filteredData[i].map(x => x.yErr)
    }

    var xValues = filteredData[0].map(x => x.run)

    var omsRuns = omsInfo.filter(x => xValues.includes(x.run))

    var fills = omsRuns.map(x => x.lhcfill)
    var durations = omsRuns.map(x => x.rundur)
    var intLumis = omsRuns.map(x => x.int_lumi)
    var times = omsRuns.map(x => [x.start_time, x.end_time])
    var plotName = getJustFilename(collection["name"])
    var yTitle = filteredData[0].length != 0 ? filteredData[0][0]["yTitle"] : ""

    if(collection.corr)
    {
        if(collection["files"].length == 2)
        {
            var yTitles = filteredData[0].length != 0 ? [filteredData[0][0]["yTitle"], filteredData[1][0]["yTitle"]] : ["", ""]
            return drawCorrelationPlot(xValues, yValues, renderTo, plotName, yTitles)
        }
        else
            return null
    }

    if(globalOptions.showXRange || globalOptions.showIntLumi)
        return drawXRangePlot(xValues, yValues, yErr, fills, durations, intLumis, renderTo, plotName, yTitle, seriesTitles)
    else if(globalOptions.showDatetime)
        return drawXRangeDatetimePlot(xValues, yValues, yErr, fills, durations, intLumis, times, renderTo, plotName, yTitle, seriesTitles)
    else
        return drawScatterPlot(xValues, yValues, yErr, fills, durations, intLumis, renderTo, plotName, yTitle, seriesTitles)
}

function drawCorrelationPlot(xValues, yValues, renderTo, plotName, yTitles)
{
    // First array contains x values and second array contains y values
    var values = yValues[0].map((v, i) => ({
        x: v,
        y: yValues[1][i],
        run: xValues[i],
        marker: {
            fillColor: colorScale((xValues[i] - xValues[0]) / (xValues[xValues.length - 1] - xValues[0])),
            radius: 4,
        }
    }))

    var options = {
        credits: {
            enabled: false
        },
        chart: {
            renderTo: renderTo,
            zoomType: "xy",
            animation: false
        },
        lang: {
            noData: "No data found for given runs"
        },
        title: {
            text: plotName
        },
        xAxis: {
            title: {
                text: yTitles[0],
            },
            max: Math.max(...values.map(i => i.x)),
            min: Math.min(...values.map(i => i.x))
        },
        yAxis: {
            title: {
                text: yTitles[1],
            },
        },
        tooltip: {
            headerFormat: "",
            pointFormat: "<b>Run No:</b> {point.run}<br><b>X</b>: {point.x}<br><b>Y</b>: {point.y}"
        },
        series: [{
                type: "scatter",
                name: "Correlation",
                data: values,
                animation: false,
                marker: {
                    symbol: "circle",
                },
                color: "#000000"
            }
        ],
        colorAxis: {
            min: xValues[0],
            max: xValues[xValues.length - 1],
            minColor: "#00FF00",
            maxColor: "#FF0000",
            stops: [
                [0, "#00FF00"],
                [0.5, "#FFFF00"],
                [1, "#FF0000"]
            ]
        },
    }

    if(globalOptions.showRegression)
    {
        options.series.push({
            type: "line",
            name: "Regression Line",
            data: linearRegression(values),
            marker: {
                enabled: false
            },
            enableMouseTracking: false,
            animation: false,
        })
    }

    var chartObj = new Highcharts.Chart(options)
    chartObj.redraw()
    chartObj.reflow()

    return chartObj
}

function drawScatterPlot(xValues, yValues, yErr, fills, durations, intLumis, renderTo, plotName, yTitle, seriesTitles) 
{
    var meanAndRms = calculateMeanAndRMS(yValues)
    var mean = meanAndRms[0]
    var rms = meanAndRms[1]
    var range = getYRange(mean, rms)
    var min_y = range[0]
    var max_y = range[1]

    var bands = getScatterFillBands(xValues, fills)

    var options = {
        credits: {
            enabled: false
        },
        chart: {
            renderTo: renderTo,
            zoomType: "xy",
            animation: false
        },
        lang: {
            noData: "No data found for given runs"
        },
        title: {
            text: plotName
        },
        subtitle: {
            text: `Mean: ${mean.toExponential(4)}, RMS: ${rms.toExponential(4)}`
        },
        xAxis: {
            title: {
                text: "Run No.",
            },
            categories: [...new Set([].concat(...xValues))], 
            plotBands: globalOptions.showFills ? bands : []
        },
        yAxis: [
            {
                title: {
                    text: yTitle,
                },
                min: min_y,
                max: max_y,
                tickPixelInterval: 60
            },
            {
                zoomEnabled: false,
                title: {
                    text: "Run Duration [sec]",
                },
                opposite: true,
                visible: globalOptions.showDurations && durations !== undefined,
                tickPixelInterval: 60
            }
        ],
        plotOptions: {
            series: {
                // Make sure legend click toggles the visibility of fill lines
                events: globalOptions.showFills ? {
                    legendItemClick: function () {
                        if (this.name == "Fills") {
                            var plotBands = this.chart.xAxis[0].plotLinesAndBands;
                            if (!this.visible) {
                                for (var i = 0; i < plotBands.length; i++) {
                                    this.chart.xAxis[0].plotLinesAndBands[i].hidden = false;
                                    $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).show();
                                }
                            }
                            else {
                                for (var i = 0; i < plotBands.length; i++) {
                                    this.chart.xAxis[0].plotLinesAndBands[i].hidden = true;
                                    $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).hide();
                                }
                            }
                        }
                    }
                } : {},
                allowPointSelect: true,
                point: {
                    events: {
                        click: function () {
                            var parent = $(this.series.chart.container).parent().parent()
                            updateLinks(parent, this.category)
                        }
                    }
                },
                marker: {
                    symbol: "circle"
                }
            },
        },
        series: globalOptions.showFills ?
            [{ // "Fills" legend item
                name: "Fills",
                color: "#e6eaf2",
                type: "area",
                legendIndex: 100
            }]
            :
            []
    }

    for(var i = 0; i < yValues.length; i++)
    {
        var tooltip = '<span style="color:{series.color}"></span><b>{point.series.name}</b><br> <b>Run No:</b> {point.category}<br/><b>'
                + yTitle + ': </b>{point.y}<br><b>Fill No:</b> {point.fill}'

        var data = []

        if (globalOptions.showDurations) 
        {
            tooltip += "<br><b>Duration:</b> {point.dur}";
            data = yValues[i].map((y, k) => ({ y: y, fill: fills[k], dur: durations[k] }));
        }
        else 
        {
            data = yValues[i].map((y, k) => ({ y: y, fill: fills[k] }))
        }
        
        tooltip += "<br>Click on the data point to reveal urls to OMS and RR.";

        options.series.push({
            name: seriesTitles[i],
            type: "scatter",
            data: data,
            borderWidth: 20,
            marker: {
                radius: 3
            },
            tooltip: {
                headerFormat: "",
                pointFormat: tooltip
            },
            showInLegend: true,
            animation: false,
            states: {
                inactive: {
                    opacity: 1
                }
            }
        })

        if (globalOptions.showErrors) 
        {
            options.series.push({
                name: "Bin Content Error",
                type: "errorbar",
                data: yValues[i].map(function(value, index) {
                    return [value - yErr[i][index], value + yErr[i][index]]
                }),
                marker: {
                    radius: 3
                },
                tooltip: {
                    headerFormat: "",
                    pointFormat: '<b>{point.series.name}</b><br> <b>Run No:</b> {point.category}<br/><b>Error Range</b> : {point.low} to {point.high}<br/>'
                },
                animation: false,
            })
        }
    }
    
    if (globalOptions.showDurations)
    {
        options.series.push({
            type: "column",
            name: "Run Duration",
            yAxis: 1,
            color: "#a8a8a8",
            zIndex: -1,
            groupPadding: 0,
            pointPadding: 0,
            borderWidth: 0,
            tooltip: {
                headerFormat: "",
                pointFormat: '<b>Run No</b>: {point.category}<br/><b>Duration</b>: {point.y}<br/>'
            },
            data: durations,
            animation: false,
            states: {
                inactive: {
                    opacity: 1
                }
            }
        })
    }
    
    var chartObj = new Highcharts.Chart(options)
    chartObj.redraw()
    chartObj.reflow()

    return chartObj
}

function drawXRangePlot(xValues, yValues, yErr, fills, durations, intLumis, renderTo, plotName, yTitle, seriesTitles) 
{
    var meanAndRms = calculateMeanAndRMS(yValues)
    var mean = meanAndRms[0]
    var rms = meanAndRms[1]
    var range = getYRange(mean, rms)
    var min_y = range[0]
    var max_y = range[1]

    var bands = getXRangeFillBands(globalOptions.showIntLumi ? intLumis : durations, fills)
    
    var options = {
        credits: {
            enabled: false
        },
        chart: {
            renderTo: renderTo,
            zoomType: "xy",
            animation: false
        },
        lang: {
            noData: "No data found for given runs"
        },
        title: {
            text: plotName
        },
        subtitle: {
            text: `Mean: ${mean.toExponential(4)}, RMS: ${rms.toExponential(4)}`
        },
        xAxis: {
            title: {
                text: "Run No.",
            },
            type: "linear",
            labels: {
                rotation: -45,
            },
            // categories: [...new Set([].concat(...xValues))],
        },
        yAxis: [
            {
                title: {
                    text: yTitle,
                },
                min: min_y,
                max: max_y,
            },
        ],
        plotOptions: {
            xrange: {
                grouping: false,
                borderRadius: 0,
            },
            series: {
                events: globalOptions.showFills ? {
                    legendItemClick: function () {
                        if (this.name == "Fills") {
                            var plotBands = this.chart.xAxis[0].plotLinesAndBands;
                            if (!this.visible) {
                                for (var i = 0; i < plotBands.length; i++) {
                                    this.chart.xAxis[0].plotLinesAndBands[i].hidden = false;
                                    $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).show();
                                }
                            }
                            else {
                                for (var i = 0; i < plotBands.length; i++) {
                                    this.chart.xAxis[0].plotLinesAndBands[i].hidden = true;
                                    $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).hide();
                                }
                            }
                        }
                    }
                } : {},
                allowPointSelect: true,
                point: {
                    events: {
                        click: function () {
                            var parent = $(this.series.chart.container).parent().parent()
                            updateLinks(parent, this.run)
                        }
                    }
                },
            }
        },
        series: globalOptions.showFills ?
            [{
                name: "Fills",
                color: "#e6eaf2",
                type: "area",
                legendIndex: 100
            }]
            :
            []
    }

    var ticks = []

    for(var i = 0; i < yValues.length; i++)
    {
        var tooltip = '<span style="color:{series.color}"></span><b>{point.series.name}'
        tooltip += "</b><br><b>Run No:</b> {point.run}"
        tooltip += `<br/><b>${yTitle} : </b>{point.y}<br><b>Fill No:</b> {point.fill}<br><b>Error:</b> {point.err}`

        var raw = []
        raw = yValues[i].map((y, k) => ({ y: y, fill: fills[k], dur: durations[k], intLumi: intLumis[k] }))

        tooltip += "<br><b>Duration:</b> {point.dur}"
        tooltip += "<br><b>Integrated luminosity:</b> {point.intLumi}"
        tooltip += "<br>Click on the data point to reveal urls to OMS and RR."
        
        var data = []
        ticks = []

        for (var j = 0; j < raw.length; j++) 
        {
            var valueForBinLength = raw[j].dur
            if(globalOptions.showIntLumi)
                valueForBinLength = raw[j].intLumi

            // Make sure bin length is not 0
            if(valueForBinLength == 0)
                valueForBinLength = 1

            var prev_x2 = get_prev_x2(j, data)
            data.push({ 
                    x: prev_x2, 
                    x2: prev_x2 + valueForBinLength, 
                    y: raw[j].y, 
                    run: xValues[j], 
                    dur: raw[j].dur, 
                    intLumi: raw[j].intLumi,
                    fill: raw[j].fill,
                    err: yErr[i][j],
                });
            ticks.push(prev_x2 + (raw[j].dur / 2));
            
            function get_prev_x2(index, arr) {
                return index === 0 ? 0 : arr[index - 1].x2;
            }
        }

        Object.assign(options.xAxis, {
            labels: {
                enabled: true,
                formatter: function () {
                    var index = ticks.indexOf(this.value);
                    var n = parseInt(ticks.length / 10);
    
                    // Show only every nth label and, always, the last one
                    if (index % n != 0 && index != ticks.length - 1)
                        return ""
    
                    return xValues[index];
                },
            },
            tickPositions: ticks,
            plotBands: globalOptions.showFills ? bands : []
        })

        options.series.push({
            name: seriesTitles[i],
            type: "xrange",
            pointWidth: 6,
            data: data,
            color: seriesColors[i],
            colorByPoint: false,
            tooltip: {
                headerFormat: "",
                pointFormat: tooltip
            },
            showInLegend: true,
            animation: false
        })

        if (globalOptions.showErrors) 
        {
            options.series.push({
                type: "xrange",
                pointWidth: 9,
                data: yErr[i].map((element, index) => {
                    return {
                        x: data[index].x,
                        x2: data[index].x2,
                        y: data[index].y + element
                    }
                }),
                color: seriesColors[i],
                colorByPoint: false,
                showInLegend: false,
                animation: false,
                enableMouseTracking: false,
                states: {
                    inactive: {
                        opacity: 1
                    }
                }
            })
    
            options.series.push({
                type: "xrange",
                pointWidth: 9,
                data: yErr[i].map((element, index) => {
                    return {
                        x: data[index].x,
                        x2: data[index].x2,
                        y: data[index].y - element
                    }
                }),
                color: seriesColors[i],
                colorByPoint: false,
                showInLegend: false,
                animation: false,
                enableMouseTracking: false,
                states: {
                    inactive: {
                        opacity: 1
                    }
                }
            })
        }
    }

    var chartObj = new Highcharts.Chart(options)
    chartObj.redraw()
    chartObj.reflow()

    return chartObj
}

function drawXRangeDatetimePlot(xValues, yValues, yErr, fills, durations, intLumis, times, renderTo, plotName, yTitle, seriesTitles)
{
    var meanAndRms = calculateMeanAndRMS(yValues)
    var mean = meanAndRms[0]
    var rms = meanAndRms[1]
    var range = getYRange(mean, rms)
    var min_y = range[0]
    var max_y = range[1]
    
    var options = {
        credits: {
            enabled: false
        },
        chart: {
            renderTo: renderTo,
            type: "xrange",
            zoomType: "xy",
            animation: false
        },
        lang: {
            noData: "No data found for given runs"
        },
        title: {
            text: plotName
        },
        subtitle: {
            text: `Mean: ${mean.toExponential(4)}, RMS: ${rms.toExponential(4)}`
        },
        xAxis: {
            title: {
                text: "Run No.",
            },
            type: "datetime",
            labels: {
                rotation: -45,
            },
        },
        yAxis: [
            {
                title: {
                    text: yTitle,
                },
                min: min_y,
                max: max_y,
            },
        ],
        plotOptions: {
            xrange: {
                grouping: false,
                borderRadius: 0,
            },
            series: {
                events: globalOptions.showFills ? {
                    legendItemClick: function () {
                        if (this.name == "Fills") {
                            var plotBands = this.chart.xAxis[0].plotLinesAndBands;
                            if (!this.visible) {
                                for (var i = 0; i < plotBands.length; i++) {
                                    this.chart.xAxis[0].plotLinesAndBands[i].hidden = false;
                                    $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).show();
                                }
                            }
                            else {
                                for (var i = 0; i < plotBands.length; i++) {
                                    this.chart.xAxis[0].plotLinesAndBands[i].hidden = true;
                                    $(this.chart.xAxis[0].plotLinesAndBands[i].svgElem.element).hide();
                                }
                            }
                        }
                    }
                } : {},
                allowPointSelect: true,
                point: {
                    events: {
                        click: function () {
                            var parent = $(this.series.chart.container).parent().parent()
                            updateLinks(parent, this.run)
                        }
                    }
                },
            }
        },
        series: globalOptions.showFills ?
            [{
                name: "Fills",
                color: "#e6eaf2",
                type: "area",
                legendIndex: 100
            }]
            :
            []
    }

    var bands = getXRangeDatetimeFillBands(fills, times)

    Object.assign(options.xAxis, {
        plotBands: globalOptions.showFills ? bands : []
    })

    for(var i = 0; i < yValues.length; i++)
    {
        var tooltip = '<span style="color:{series.color}"></span><b>{point.series.name}'
        tooltip += "</b><br><b>Run No:</b> {point.run}"
        tooltip += `<br/><b>${yTitle} : </b>{point.y}<br><b>Fill No:</b> {point.fill}<br><b>Error:</b> {point.err}`

        var raw = yValues[i].map((y, k) => (
            { 
                y: y, 
                fill: fills[k], 
                dur: durations[k], 
                intLumi: intLumis[k], 
                startTime: new Date(safeGetAtIndex(times[k], 0)), 
                endTime: new Date(safeGetAtIndex(times[k], 1)),
            }))

        tooltip += "<br><b>Duration:</b> {point.dur}"
        tooltip += "<br><b>Integrated luminosity:</b> {point.intLumi}"
        tooltip += "<br><b>Start time:</b> {point.startTime}"
        tooltip += "<br><b>End time:</b> {point.endTime}"
        tooltip += "<br>Click on the data point to reveal urls to OMS and RR."
        
        var data = []
        ticks = []

        for (var j = 0; j < raw.length; j++) 
        {
            data.push({
                    x: raw[j].startTime.getTime(), 
                    x2: raw[j].endTime.getTime(), 
                    y: raw[j].y, 
                    run: xValues[j], 
                    dur: raw[j].dur, 
                    intLumi: raw[j].intLumi,
                    startTime: raw[j].startTime,
                    endTime: raw[j].endTime,
                    fill: raw[j].fill,
                    err: yErr[i][j],
                })
        }        

        options.series.push({
            name: seriesTitles[i],
            type: "xrange",
            pointWidth: 6,
            data: data,
            color: seriesColors[i],
            colorByPoint: false,
            tooltip: {
                headerFormat: "",
                pointFormat: tooltip
            },
            showInLegend: true,
            animation: false
        })

        if (globalOptions.showErrors) 
        {
            options.series.push({
                type: "xrange",
                pointWidth: 9,
                data: yErr[i].map((element, index) => {
                    return {
                        x: data[index].x,
                        x2: data[index].x2,
                        y: data[index].y + element
                    }
                }),
                color: seriesColors[i],
                colorByPoint: false,
                showInLegend: false,
                animation: false,
                enableMouseTracking: false,
                states: {
                    inactive: {
                        opacity: 1
                    }
                }
            })
    
            options.series.push({
                type: "xrange",
                pointWidth: 9,
                data: yErr[i].map((element, index) => {
                    return {
                        x: data[index].x,
                        x2: data[index].x2,
                        y: data[index].y - element
                    }
                }),
                color: seriesColors[i],
                colorByPoint: false,
                showInLegend: false,
                animation: false,
                enableMouseTracking: false,
                states: {
                    inactive: {
                        opacity: 1
                    }
                }
            })
        }
    }

    var chartObj = new Highcharts.Chart(options)
    chartObj.redraw()
    chartObj.reflow()

    return chartObj
}

function getScatterFillBands(xValues, fills)
{
    var bands = []
    var start_i = 0
    var lastFill = 0
    var flag = false

    for (var i = 0; i < xValues.length; i++) 
    {
        if (fills[i] !== lastFill)
        {
            if (flag) {
                bands.push({
                    color: "#e6eaf2",
                    from: start_i - 0.5,
                    to: i - 1 + 0.5,
                    id: "fills"
                });
            }
            else 
                start_i = i;
            
            flag = !flag
            lastFill = fills[i]
        }
    }

    // Add last fill if needed
    if (flag) 
    {
        bands.push({
            color: "#e6eaf2",
            from: start_i - 0.5,
            to: i - 1 + 0.5,
            id: "fills"
        })
    }

    return bands
}

function getXRangeFillBands(durations, fills)
{
    if(fills.length == 0 || durations.length == 0)
        return []

    // Group by fill and sum durations
    var bands = []
    var lastFill = fills[0]
    var durSum = 0
    var lastDurSum = 0;

    for(var j = 0; j < fills.length; j++)
    {
        if(fills[j] != lastFill)
        {
            bands.push({color: "#e6eaf2", from: lastDurSum, to: durSum, id: "fills"})
            lastDurSum = durSum
            lastFill = fills[j]
        }

        durSum += durations[j]
    }
    
    // Add last fill
    bands.push({color: "#e6eaf2", from: lastDurSum, to: durSum, id: "fills"})

    // Remove every second
    bands = bands.filter(function(_, i) {
        return i % 2 === 0;
    })

    return bands
}

function getXRangeDatetimeFillBands(fills, times)
{
    if(fills.length == 0 || times.length == 0)
        return []
    
    times = times.map(x => x.map(x1 => new Date(x1).getTime()))

    var bands = []
    var lastFill = fills[0]
    var lastTime = times[0][0]

    for(var j = 0; j < fills.length - 1; j++)
    {
        if(fills[j] != lastFill)
        {
            bands.push({color: "#e6eaf2", from: lastTime, to: times[j - 1][1], id: "fills"})
            lastFill = fills[j]
            lastTime = times[j][0]
        }
    }
    
    // Add last fill
    bands.push({color: "#e6eaf2", from: lastTime, to: times[times.length - 1][1], id: "fills"})

    return bands
}
