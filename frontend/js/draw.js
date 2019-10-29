
const plotter = (function() {
    return {

        draw: async function(plotData, renderTo) 
        {
            // console.log(plotData)
            if(plotData.correlation) 
            {
                if(plotData.series.length === 2)
                    return this.drawCorrelationPlot(plotData, renderTo)
                else
                    return null
            }

            if(optionsController.options.showXRange || optionsController.options.showIntLumi)
                return this.drawXRangePlot(plotData, renderTo)
            else if(optionsController.options.showDatetime)
                return this.drawXRangeDatetimePlot(plotData, renderTo)
            else
                return this.drawScatterPlot(plotData, renderTo)
        },

        drawCorrelationPlot: function(plotData, renderTo)
        {
            const plotName = plotData.plot_title
            const xValues = plotData.series[0].trends.map(x => x.run)
            const yValues = plotData.series.map(x => x.trends.map(y => y.value))
            const seriesTitles = plotData.series.map(x => x.metadata.y_title)

            // First array contains x values and second array contains y values
            var values = yValues[0].map((v, i) => ({
                x: v,
                y: yValues[1][i],
                run: xValues[i],
                marker: {
                    fillColor: helpers.colorScale((xValues[i] - xValues[0]) / (xValues[xValues.length - 1] - xValues[0])),
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
                subtitle: {
                    text: `<i>${plotData.name}</i>`
                },
                xAxis: {
                    title: {
                        text: seriesTitles[0],
                    },
                    max: Math.max(...values.map(i => i.x)),
                    min: Math.min(...values.map(i => i.x))
                },
                yAxis: {
                    title: {
                        text: seriesTitles[1],
                    },
                },
                tooltip: {
                    headerFormat: "",
                    pointFormat: "<b>Run No sdsdsd:</b> {point.run}<br><b>X</b>: {point.x}<br><b>Y</b>: {point.y}",
                    style : { opacity: 0.9 },
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

            if(optionsController.options.showRegression)
            {
                options.series.push({
                    type: "line",
                    name: "Regression Line",
                    data: helpers.linearRegression(values),
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
        },

        drawScatterPlot: function(plotData, renderTo) 
        {
            const plotName = plotData.plot_title
            const yTitle = plotData.y_title
            const xValues = plotData.series[0].trends.map(x => x.run)
            const yValues = plotData.series.map(x => x.trends.map(y => y.value))
            const yErr = plotData.series.map(x => x.trends.map(y => y.error))
            const fills = plotData.series[0].trends.map(x => x.oms_info.fill_number)
            const durations = plotData.series[0].trends.map(x => x.oms_info.duration)
            const seriesTitles = plotData.series.map(x => x.metadata.y_title)

            const meanAndRms = helpers.calculateMeanAndRMS(yValues)
            const mean = meanAndRms[0]
            const rms = meanAndRms[1]
            const range = helpers.getYRange(mean, rms)
            const min_y = range[0]
            const max_y = range[1]

            const bands = this.getScatterFillBands(xValues, fills)

            const options = {
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
                    text: `<i>${plotData.name}</i><br>Mean: ${mean.toExponential(4)}, RMS: ${rms.toExponential(4)}`
                },
                tooltip: {
                    style : { opacity: 0.9 },
                },
                xAxis: {
                    title: {
                        text: "Run No.",
                    },
                    categories: [...new Set([].concat(...xValues))], 
                    plotBands: optionsController.options.showFills ? bands : []
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
                            text: "Run Duration (sec)",
                        },
                        opposite: true,
                        visible: optionsController.options.showDurations && durations !== undefined,
                        tickPixelInterval: 60
                    }
                ],
                plotOptions: {
                    series: {
                        // Make sure legend click toggles the visibility of fill lines
                        events: optionsController.options.showFills ? {
                            legendItemClick: function () {
                                if (this.name === "Fills") {
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
                                    const parent = $(this.series.chart.container).parent().parent()
                                    main.updateLinks(parent, plotData, this.category, this.series.index - 1)
                                }
                            }
                        },
                        marker: {
                            symbol: "circle"
                        }
                    },
                },
                series: optionsController.options.showFills ?
                    [{ // "Fills" legend item
                        name: "Fills",
                        color: "#e6eaf2",
                        type: "area",
                        legendIndex: 100
                    }]
                    :
                    []
            }

            for(let i = 0; i < plotData.series.length; i++)
            {
                const tooltip = `
                    <b>{point.series.name}</b><br> 
                    <b>${yTitle}: </b>{point.y}<br>
                    <b>Error:</b> {point.error}<br/>
                    <b>Run No:</b> {point.run}<br/>
                    <b>Fill No:</b> {point.fill_number}<br>
                    <b>Duration:</b> {point.duration}<br>
                    <b>Delivered luminosity:</b> {point.del_lumi}<br>
                    <b>B field:</b> {point.b_field}<br>
                    <b>End luminosity:</b> {point.end_lumi}<br>
                    <b>Start time:</b> {point.start_time}<br>
                    <b>End time:</b> {point.end_time}<br>
                    <b>Energy:</b> {point.energy}<br>
                    <b>Era:</b> {point.era}<br>
                    <b>Injection scheme:</b> {point.injection_scheme}<br>
                    <b>HLT key:</b> {point.hlt_key}<br>
                    <b>HLT physics rate:</b> {point.hlt_physics_rate}<br>
                    <b>L1T key:</b> {point.l1_key}<br>
                    <b>L1T rate:</b> {point.l1_rate}<br>
                    <b>Recorded lumi:</b> {point.recorded_lumi}<br>
                    Click on the data point to reveal urls to OMS, RR and DQM GUI.`

                const data = plotData.series[i].trends.map(trend => ({
                    y:                  trend.value,
                    error:              trend.error,
                    run:                trend.run,
                    del_lumi:           trend.oms_info.delivered_lumi,
                    b_field:            trend.oms_info.b_field,
                    duration:           trend.oms_info.duration,
                    end_lumi:           trend.oms_info.end_lumi,
                    end_time:           trend.oms_info.end_time,
                    energy:             trend.oms_info.energy,
                    era:                trend.oms_info.era,
                    fill_number:        trend.oms_info.fill_number,
                    hlt_key:            trend.oms_info.hlt_key,
                    hlt_physics_rate:   trend.oms_info.hlt_physics_rate,
                    injection_scheme:   trend.oms_info.injection_scheme,
                    l1_key:             trend.oms_info.l1_key,
                    l1_rate:            trend.oms_info.l1_rate,
                    recorded_lumi:      trend.oms_info.recorded_lumi,
                    start_time:         trend.oms_info.start_time,
                }))

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
                        pointFormat: tooltip,
                    },
                    showInLegend: true,
                    animation: false,
                    states: {
                        inactive: {
                            opacity: 1
                        },
                    }
                })

                if (optionsController.options.showErrors) 
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
            
            if (optionsController.options.showDurations)
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
                        },
                    },
                })
            }
            
            const chartObj = new Highcharts.Chart(options)
            chartObj.redraw()
            chartObj.reflow()

            return chartObj
        },

        drawXRangePlot: function(plotData, renderTo) 
        {
            const plotName = plotData.plot_title
            const yTitle = plotData.y_title
            const xValues = plotData.series[0].trends.map(x => x.run)
            const yValues = plotData.series.map(x => x.trends.map(y => y.value))
            const yErr = plotData.series.map(x => x.trends.map(y => y.error))
            const fills = plotData.series[0].trends.map(x => x.oms_info.fill_number)
            const durations = plotData.series[0].trends.map(x => x.oms_info.duration)
            const intLumis = plotData.series[0].trends.map(x => x.oms_info.init_lumi)
            const seriesTitles = plotData.series.map(x => x.metadata.y_title)

            const meanAndRms = helpers.calculateMeanAndRMS(yValues)
            const mean = meanAndRms[0]
            const rms = meanAndRms[1]
            const range = helpers.getYRange(mean, rms)
            const min_y = range[0]
            const max_y = range[1]

            const bands = this.getXRangeFillBands(optionsController.options.showIntLumi ? intLumis : durations, fills)
            
            const options = {
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
                    text: `<i>${plotData.name}</i><br>Mean: ${mean.toExponential(4)}, RMS: ${rms.toExponential(4)}`
                },
                tooltip: {
                    style : { opacity: 0.9 },
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
                        events: optionsController.options.showFills ? {
                            legendItemClick: function () {
                                if (this.name === "Fills") {
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
                                    const parent = $(this.series.chart.container).parent().parent()
                                    main.updateLinks(parent, plotData, this.run, this.series.index - 1)
                                }
                            }
                        },
                    }
                },
                series: optionsController.options.showFills ?
                    [{
                        name: "Fills",
                        color: "#e6eaf2",
                        type: "area",
                        legendIndex: 100
                    }]
                    :
                    []
            }

            for(let i = 0; i < plotData.series.length; i++)
            {
                const tooltip = `
                    <b>{point.series.name}</b><br> 
                    <b>${yTitle}: </b>{point.y}<br>
                    <b>Error:</b> {point.error}<br/>
                    <b>Run No:</b> {point.run}<br/>
                    <b>Fill No:</b> {point.fill_number}<br>
                    <b>Duration:</b> {point.duration}<br>
                    <b>Delivered luminosity:</b> {point.del_lumi}<br>
                    <b>B field:</b> {point.b_field}<br>
                    <b>End luminosity:</b> {point.end_lumi}<br>
                    <b>Start time:</b> {point.start_time}<br>
                    <b>End time:</b> {point.end_time}<br>
                    <b>Energy:</b> {point.energy}<br>
                    <b>Era:</b> {point.era}<br>
                    <b>Injection scheme:</b> {point.injection_scheme}<br>
                    <b>HLT key:</b> {point.hlt_key}<br>
                    <b>HLT physics rate:</b> {point.hlt_physics_rate}<br>
                    <b>L1T key:</b> {point.l1_key}<br>
                    <b>L1T rate:</b> {point.l1_rate}<br>
                    <b>Recorded lumi:</b> {point.recorded_lumi}<br>
                    Click on the data point to reveal urls to OMS, RR and DQM GUI.`

                const data = plotData.series[i].trends.map(trend => ({
                    y:                  trend.value,
                    error:              trend.error,
                    run:                trend.run,
                    del_lumi:           trend.oms_info.delivered_lumi,
                    b_field:            trend.oms_info.b_field,
                    duration:           trend.oms_info.duration,
                    end_lumi:           trend.oms_info.end_lumi,
                    end_time:           trend.oms_info.end_time,
                    energy:             trend.oms_info.energy,
                    era:                trend.oms_info.era,
                    fill_number:        trend.oms_info.fill_number,
                    hlt_key:            trend.oms_info.hlt_key,
                    hlt_physics_rate:   trend.oms_info.hlt_physics_rate,
                    injection_scheme:   trend.oms_info.injection_scheme,
                    l1_key:             trend.oms_info.l1_key,
                    l1_rate:            trend.oms_info.l1_rate,
                    recorded_lumi:      trend.oms_info.recorded_lumi,
                    start_time:         trend.oms_info.start_time,
                }))

                const ticks = []

                for (var j = 0; j < data.length; j++) 
                {
                    let valueForBinLength = data[j].duration
                    if(optionsController.options.showIntLumi)
                        valueForBinLength = data[j].del_lumi

                    // Make sure bin length is not 0
                    if(valueForBinLength === 0)
                        valueForBinLength = 1

                    const prev_x2 = get_prev_x2(j, data)
                    data[j].x = prev_x2
                    data[j].x2 = prev_x2 + valueForBinLength

                    ticks.push(prev_x2 + (data[j].dur / 2));
                    
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
                    plotBands: optionsController.options.showFills ? bands : []
                })

                options.series.push({
                    name: seriesTitles[i],
                    type: "xrange",
                    pointWidth: 6,
                    data: data,
                    color: helpers.seriesColors[i],
                    colorByPoint: false,
                    tooltip: {
                        headerFormat: "",
                        pointFormat: tooltip,
                    },
                    showInLegend: true,
                    animation: false
                })

                if (optionsController.options.showErrors) 
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
                        color: helpers.seriesColors[i],
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
                        color: helpers.seriesColors[i],
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

            const chartObj = new Highcharts.Chart(options)
            chartObj.redraw()
            chartObj.reflow()

            return chartObj
        },

        drawXRangeDatetimePlot: function(plotData, renderTo)
        {
            const plotName = plotData.plot_title
            const yTitle = plotData.y_title
            const xValues = plotData.series[0].trends.map(x => x.run)
            const yValues = plotData.series.map(x => x.trends.map(y => y.value))
            const yErr = plotData.series.map(x => x.trends.map(y => y.error))
            const fills = plotData.series[0].trends.map(x => x.oms_info.fill_number)
            const durations = plotData.series[0].trends.map(x => x.oms_info.duration)
            const intLumis = plotData.series[0].trends.map(x => x.oms_info.init_lumi)
            const times = plotData.series[0].trends.map(x => [x.oms_info.start_time, x.oms_info.end_time])
            const seriesTitles = plotData.series.map(x => x.metadata.y_title)

            const meanAndRms = helpers.calculateMeanAndRMS(yValues)
            const mean = meanAndRms[0]
            const rms = meanAndRms[1]
            const range = helpers.getYRange(mean, rms)
            const min_y = range[0]
            const max_y = range[1]
            
            const options = {
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
                    text: `<i>${plotData.name}</i><br>Mean: ${mean.toExponential(4)}, RMS: ${rms.toExponential(4)}`
                },
                tooltip: {
                    style : { opacity: 0.9 },
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
                        events: optionsController.options.showFills ? {
                            legendItemClick: function () {
                                if (this.name === "Fills") {
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
                                    const parent = $(this.series.chart.container).parent().parent()
                                    main.updateLinks(parent, plotData, this.run, this.series.index - 1)
                                }
                            }
                        },
                    }
                },
                series: optionsController.options.showFills ?
                    [{
                        name: "Fills",
                        color: "#e6eaf2",
                        type: "area",
                        legendIndex: 100
                    }]
                    :
                    []
            }

            const bands = this.getXRangeDatetimeFillBands(fills, times)

            Object.assign(options.xAxis, {
                plotBands: optionsController.options.showFills ? bands : []
            })

            for(let i = 0; i < plotData.series.length; i++)
            {
                const tooltip = `
                    <b>{point.series.name}</b><br> 
                    <b>${yTitle}: </b>{point.y}<br>
                    <b>Error:</b> {point.error}<br/>
                    <b>Run No:</b> {point.run}<br/>
                    <b>Fill No:</b> {point.fill_number}<br>
                    <b>Duration:</b> {point.duration}<br>
                    <b>Delivered luminosity:</b> {point.del_lumi}<br>
                    <b>B field:</b> {point.b_field}<br>
                    <b>End luminosity:</b> {point.end_lumi}<br>
                    <b>Start time:</b> {point.start_time}<br>
                    <b>End time:</b> {point.end_time}<br>
                    <b>Energy:</b> {point.energy}<br>
                    <b>Era:</b> {point.era}<br>
                    <b>Injection scheme:</b> {point.injection_scheme}<br>
                    <b>HLT key:</b> {point.hlt_key}<br>
                    <b>HLT physics rate:</b> {point.hlt_physics_rate}<br>
                    <b>L1T key:</b> {point.l1_key}<br>
                    <b>L1T rate:</b> {point.l1_rate}<br>
                    <b>Recorded lumi:</b> {point.recorded_lumi}<br>
                    Click on the data point to reveal urls to OMS, RR and DQM GUI.`

                const data = plotData.series[i].trends.map(trend => ({
                    x:                  new Date(trend.oms_info.start_time).getTime(), 
                    x2:                 new Date(trend.oms_info.end_time).getTime(), 
                    y:                  trend.value,
                    error:              trend.error,
                    run:                trend.run,
                    del_lumi:           trend.oms_info.delivered_lumi,
                    b_field:            trend.oms_info.b_field,
                    duration:           trend.oms_info.duration,
                    end_lumi:           trend.oms_info.end_lumi,
                    end_time:           trend.oms_info.end_time,
                    energy:             trend.oms_info.energy,
                    era:                trend.oms_info.era,
                    fill_number:        trend.oms_info.fill_number,
                    hlt_key:            trend.oms_info.hlt_key,
                    hlt_physics_rate:   trend.oms_info.hlt_physics_rate,
                    injection_scheme:   trend.oms_info.injection_scheme,
                    l1_key:             trend.oms_info.l1_key,
                    l1_rate:            trend.oms_info.l1_rate,
                    recorded_lumi:      trend.oms_info.recorded_lumi,
                    start_time:         trend.oms_info.start_time,
                }))  

                options.series.push({
                    name: seriesTitles[i],
                    type: "xrange",
                    pointWidth: 6,
                    data: data,
                    color: helpers.seriesColors[i],
                    colorByPoint: false,
                    tooltip: {
                        headerFormat: "",
                        pointFormat: tooltip
                    },
                    showInLegend: true,
                    animation: false
                })

                if (optionsController.options.showErrors) 
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
                        color: helpers.seriesColors[i],
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
                        color: helpers.seriesColors[i],
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

            const chartObj = new Highcharts.Chart(options)
            chartObj.redraw()
            chartObj.reflow()

            return chartObj
        },

        getScatterFillBands: function(xValues, fills)
        {
            const bands = []
            let start_i = 0
            let lastFill = 0
            let flag = false

            for (let i = 0; i < xValues.length; i++) 
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
                    to: xValues.length - 1 + 0.5,
                    id: "fills"
                })
            }

            return bands
        },

        getXRangeFillBands: function(durations, fills)
        {
            if(fills.length === 0 || durations.length === 0)
                return []

            // Group by fill and sum durations
            let bands = []
            let lastFill = fills[0]
            let durSum = 0
            let lastDurSum = 0;

            for(let j = 0; j < fills.length; j++)
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
        },

        getXRangeDatetimeFillBands: function(fills, times)
        {
            if(fills.length === 0 || times.length === 0)
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
    }
}())
