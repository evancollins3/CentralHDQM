
var omsInfo = {}
var collections = []
var directoryPlotFiles = []
const plotsPerPage = 4
var chartsObjects = []
var popupChartObject = undefined
var popupChartIndex = 0
var currentPage = 1

var initialStartX = 0
var initialEndX = 0
var initialStartY = 0
var initialEndY = 0

var drawArguments = []

async function submitClicked(event)
{
    event.preventDefault()
    await submit(1)
}

async function submit(page)
{
    if($("#filter-select").val() == "json")
    {
        if($("#filter-input-file")[0].files.length == 0)
            return
    }

    $("#pagination-container").removeClass("d-none")
    clearLinks()

    $("#show-plot-list-button").removeAttr("disabled")

    // Read global options
    readOptionValues()

    directoryPlotFiles = getFileListForCurrentSelection()
    await displayPage(page)
    drawPlotList()
    drawPageSelector()
    changeUrlToReflectSettings()
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

        var file = directoryPlotFiles[((page - 1) * plotsPerPage) + i]
        var collection = getCollectionForFile(file)
        var data = []

        for(var j = 0; j < collection["files"].length; j++)
        {
            var filename = getJustDirname(file) + collection["files"][j] + ".json"
            var response = await fetch(filename, {
                credentials: "same-origin"
            })
            var fileData = await response.json()

            data[j] = fileData[Object.keys(fileData)[0]]
        }
        
        var renderTo = `plot-container-${i}`

        var chartObj = await draw(collection, data, renderTo)
        chartsObjects.push(chartObj)
        drawArguments.push([collection, data, renderTo])
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
    event.preventDefault()
    window.scrollTo(0, 0)

    displayPage(page)
    drawPageSelector()
    addUrlVariable("page", page)
}

function drawPlotList()
{
    const divStart = `<div class="col-auto mr-2 ml-2 d-inline-block align-top">`
    const divEnd = `</div></div>`
    var html = ""
    var column = ""

    for(var i = 0; i < directoryPlotFiles.length; i++)
    {
        column += `<div class="row">${getJustFilename(directoryPlotFiles[i])}</div>`
        if((i + 1) % 4 == 0 || i == directoryPlotFiles.length - 1)
        {
            var pageNumber = Math.ceil((i + 1) / 4)
            var pageTitle = `<a class="row small font-italic" href="#" onclick="pageSelected(event, ${pageNumber})">Page ${pageNumber}</a>`
            html += divStart + pageTitle + column + divEnd
            column = ""
        }
    }

    if(directoryPlotFiles.length == 0)
        html = `<div class="ml-2">No plots found</div>`

    $("#plot-list-container").html(html)
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

async function changeRangesClicked(plotIndex)
{
    popupChartIndex = plotIndex

    var collection = drawArguments[plotIndex][0]
    var data = drawArguments[plotIndex][1]
    var renderTo = 'change-ranges-container'

    if(popupChartObject != undefined)
        popupChartObject.destroy()
    
    popupChartObject = await draw(collection, data, renderTo)

    var filteredData = await getFilteredArray(data[0])

    initialStartX = filteredData[0].run
    initialEndX = filteredData[filteredData.length - 1].run
    initialStartY = popupChartObject.yAxis[0].min
    initialEndY = popupChartObject.yAxis[0].max

    $("#start-x").val(initialStartX)
    $("#end-x").val(initialEndX)
    $("#start-y").val(initialStartY)
    $("#end-y").val(initialEndY)

    $('#change-ranges-modal').modal('show')

    addUrlVariable("modalPlot", plotIndex)
}

async function popupSubmitClicked()
{
    var start_x = $("#start-x").val()
    var end_x = $("#end-x").val()
    var start_y = $("#start-y").val()
    var end_y = $("#end-y").val()

    if(start_x != initialStartX || end_x != initialEndX)
    {
        // X range changed
        var collection = drawArguments[popupChartIndex][0]
        var data = drawArguments[popupChartIndex][1]
        var renderTo = 'change-ranges-container'

        if(popupChartObject != undefined)
            popupChartObject.destroy()
        
        popupChartObject = await draw(collection, data, renderTo, list => 
        {
            return list.filter(x => x.run >= start_x && x.run <= end_x)
        })
    }
    if(start_y != initialStartY || end_y != initialEndY)
    {
        // Y range changed
        popupChartObject.yAxis[0].update(
        {
            min: start_y,
            max: end_y
        })
    }

    $("#start-y").val(popupChartObject.yAxis[0].min)
    $("#end-y").val(popupChartObject.yAxis[0].max)

    initialStartX = start_x
    initialEndX = end_x
    initialStartY = start_y
    initialEndY = end_y
}

function changeUrlToReflectSettings()
{
    // Data argument
    var values = $("#data-selection-container").find("select").map((_, x) => x.value).toArray()
    addUrlVariable("data", values.join(","))

    // Filter
    addUrlVariable("filter", $("#filter-select").val())
    addUrlVariable("filterValue", getFilterValue())

    // Options
    var optionsBitSum = getBitwiseSum()
    addUrlVariable("options", optionsBitSum)

    // Search query
    var searchQuery = $("#search-query-input").val()
    if(searchQuery == null || searchQuery == "")
        deleteUrlVariable("search")
    else
        addUrlVariable("search", $("#search-query-input").val())

    // Page
    addUrlVariable("page", currentPage)
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

$('#change-ranges-modal').on('hide.bs.modal', function (e)
{
    deleteUrlVariable("modalPlot")
})

$(document).ready(async function()
{
    const response1 = await fetch("./data/oms_info.json", {
        credentials: "same-origin"
    })
    omsInfo = await response1.json()

    const response2 = await fetch("./data/collections.json", {
        credentials: "same-origin"
    })
    collections = await response2.json()

    // Safe to click submit now
    $("#submit-button").removeAttr("disabled")
    $("#submit-button-spinner").hide()
    $("#submit-button-title").show()

    if(hasUrlVariable("data"))
    {
        if(hasUrlVariable("page"))
            currentPage = getUrlVariable("page")
        
        await submit(currentPage)
    }

    if(hasUrlVariable("modalPlot"))
    {
        await changeRangesClicked(getUrlVariable("modalPlot"))
    }

    // http://vocms0183.cern.ch/agg/api/v1/runs/meta
    // http://vocms0183.cern.ch/agg/api/v1/runs?fields=recorded_lumi&page[limit]=1000
    // http://vocms0183.cern.ch/agg/api/v1/runs?fields=run_number,fill_number,duration,start_time&sort=-run_number&page[limit]=1000
    // EQ, LT, LE, GT, GE
    // http://vocms0183.cern.ch/agg/api/v1/runs?fields=run_number,fill_number,duration,start_time&sort=-run_number&page[limit]=1000&filter[run_number][GE]=250000&filter[run_number][LE]=250100
})
