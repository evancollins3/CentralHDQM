
var omsInfo = {}
var collections = []
var directoryPlotFiles = []
const plotsPerPage = 4
var chartsObjects = []
var popupChartObject = {}
var currentPage = 1

var drawArguments = []

function submitClicked(event)
{
    event.preventDefault()

    $("#pagination-container").removeClass("d-none")
    clearLinks()

    // Read global options
    readCheckboxOptionValues()

    directoryPlotFiles = getFileListForCurrentSelection()
    displayPage(1)
    drawPageSelector()
}

async function displayPage(page)
{
    destroyAllPresentPlots()
    currentPage = page

    var numberOfPastPlots = (page - 1) * plotsPerPage
    var numberOfFuturePlots = directoryPlotFiles.length - numberOfPastPlots
    var numberOfPlotsToPresent = Math.min(plotsPerPage, numberOfFuturePlots)
    
    for(var i = 0; i < numberOfPlotsToPresent; i++)
    {
        $(`#plot-card-${i}`).removeClass("d-none")

        var filteredData = []

        var seriesTitles = []
        var xValues = []
        var yValues = []
        var yErr = []

        var file = directoryPlotFiles[((page - 1) * plotsPerPage) + i]

        var collection = getCollectionForFile(file)
        for(var j = 0; j < collection["files"].length; j++)
        {
            var filename = getJustDirname(file) + collection["files"][j] + ".json"
            var response = await fetch(filename)
            var fileData = await response.json()

            // Apply run ranges based on selected filter
            var array = await getFilteredArray(fileData)

            filteredData[j] = array
            
            // Try changing the title only if there are multiple series in the plot
            if(collection["files"].length == 1)
                seriesTitles[j] = collection["files"][j]
            else
                seriesTitles[j] = getSeriesTitleByFilename(collection["files"][j])

            yValues[j] = array.map(x => x.y)
            yErr[j] = array.map(x => x.yErr)
        }

        xValues = filteredData[0].map(x => x.run)

        var fills = []
        var durations = []
        var intLumis = []
        var times = []
        var plotName = getJustFilename(collection["name"])
        var yTitle = filteredData[0][0]['yTitle']
        var renderTo = `plot-container-${i}`

        var omsRuns = omsInfo.filter(x => xValues.includes(x.run))
        fills = omsRuns.map(x => x.lhcfill)
        durations = omsRuns.map(x => x.rundur)
        intLumis = omsRuns.map(x => x.int_lumi)
        times = omsRuns.map(x => [x.start_time, x.end_time])

        var chartObj = draw(xValues, yValues, yErr, fills, durations, intLumis, times, renderTo, plotName, yTitle, seriesTitles)
        chartsObjects.push(chartObj)
        drawArguments.push([xValues, yValues, yErr, fills, durations, intLumis, times, renderTo, plotName, yTitle, seriesTitles])
    }

    for(var i = numberOfPlotsToPresent; i < plotsPerPage; i++)
    {
        $(`#plot-card-${i}`).addClass("d-none")
    }
}

function getCollectionForFile(file)
{
    var justFilename = getJustFilename(file)
    var collection = collections.find(x => x["name"] == justFilename)
    if(collection == undefined)
    {
        collection = 
        {
            files: [ justFilename ], 
            name: file, 
            corr: false
        }
    }

    return collection
}

function pageSelected(event, page)
{
    // event.preventDefault()
    displayPage(page)
    drawPageSelector()
}

function drawPageSelector()
{
    var numberOfPages = Math.ceil(directoryPlotFiles.length / plotsPerPage)
    var html = ""

    for(var i = 1; i <= numberOfPages; i++)
    {
        if(i == currentPage)
            html += `<li class="page-item active"><a class="page-link">${i}</a></li>`
        else
            html += `<li class="page-item"><a class="page-link" href="#" onclick="pageSelected(event, ${i})">${i}</a></li>`
    }

    $("#pagination-ul").html(html)
}

function updateLinks(parent, run_nr) 
{
    var linksInfo = parent.find(".links-info")
    var omsLink = parent.find(".oms-link")
    var rrLink = parent.find(".rr-link")

    linksInfo.text("View run " + run_nr + " in:")
    omsLink.text("OMS")
    rrLink.text("RR")
    
    omsLink.attr("href", "https://cmsoms.cern.ch/cms/runs/report?cms_run=" + run_nr)
    rrLink.attr("href", "https://cmsrunregistry.web.cern.ch/offline/workspaces/global?run_number=" + run_nr)
}

function clearLinks()
{
    for(var i = 0; i < plotsPerPage; i++)
    {
        var parent = $(`#plot-card-${i}`)

        var linksInfo = parent.find(".links-info")
        var omsLink = parent.find(".oms-link")
        var rrLink = parent.find(".rr-link")

        linksInfo.text("")
        omsLink.text("")
        rrLink.text("")
        omsLink.attr("href", "")
        rrLink.attr("href", "")
    }
}

function changeRangesClicked(plotIndex)
{
    var xValues = drawArguments[plotIndex][0]
    var yValues = drawArguments[plotIndex][1]
    var yErr = drawArguments[plotIndex][2]
    var fills = drawArguments[plotIndex][3]
    var durations = drawArguments[plotIndex][4]
    var intLumis = drawArguments[plotIndex][5]
    var times = drawArguments[plotIndex][6]
    var renderTo = 'change-ranges-container'
    var plotName = drawArguments[plotIndex][8]
    var yTitle = drawArguments[plotIndex][9]
    var seriesTitles = drawArguments[plotIndex][10]

    popupChartObject = draw(xValues, yValues, yErr, fills, durations, intLumis, times, renderTo, plotName, yTitle, seriesTitles)

    $("#start-x").val(xValues[0])
    $("#end-x").val(xValues[xValues.length - 1])

    $("#start-y").val(popupChartObject.yAxis[0].min);
    $("#end-y").val(popupChartObject.yAxis[0].max)

    $('.change-ranges-modal').modal('show')
}

function popupSubmitClicked()
{
    var start_x = $("#start-x").val()
    var end_x = $("#end-x").val()
    var start_y = $("#start-y").val()
    var end_y = $("#end-y").val()
    
    popupChartObject.yAxis[0].update(
    {
        min: start_y,
        max: end_y
    })

    var min_x = 0
    var max_x = 0

    popupChartObject.xAxis[0].categories.forEach((value, index) => 
    {
        if(value < start_x)
            min_x = index + 1
        if(value <= end_x)
            max_x = index
    })

    popupChartObject.xAxis[0].update(
    {
        min: min_x,
        max: max_x
    })
}

function destroyAllPresentPlots()
{
    chartsObjects.forEach(x => 
    {
        try 
        {
            x.destroy()
        }
        catch(error)
        {
            console.error(error);
        }
    })
    chartsObjects = []
    drawArguments = []
}

$(document).ready(async function()
{
    const response1 = await fetch("./data/oms_info.json")
    omsInfo = await response1.json()

    const response2 = await fetch("./data/collections.json")
    collections = await response2.json()

    // Safe to click submit now
    $("#submit-button").removeAttr("disabled")

    // http://vocms0183.cern.ch/agg/api/v1/runs/meta
    // http://vocms0183.cern.ch/agg/api/v1/runs?fields=recorded_lumi&page[limit]=1000
    // http://vocms0183.cern.ch/agg/api/v1/runs?fields=run_number,fill_number,duration,start_time&sort=-run_number&page[limit]=1000
    // EQ, LT, LE, GT, GE
    // http://vocms0183.cern.ch/agg/api/v1/runs?fields=run_number,fill_number,duration,start_time&sort=-run_number&page[limit]=1000&filter[run_number][GE]=250000&filter[run_number][LE]=250100
})
