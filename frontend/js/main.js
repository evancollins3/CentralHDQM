
// var omsInfo = {}
// var collections = []
// var directoryPlotFiles = []
// const plotsPerPage = 4
// var chartsObjects = []
// var popupChartObject = undefined
// var popupChartIndex = 0
// var currentPage = 1

// var initialStartX = 0
// var initialEndX = 0
// var initialStartY = 0
// var initialEndY = 0

// var drawArguments = []

// async function submitClicked(event)
// {
//     event.preventDefault()
//     await submit(1)
// }

// async function submit(page)
// {
//     if($("#filter-select").val() == "json")
//     {
//         if($("#filter-input-file")[0].files.length == 0)
//             return
//     }

//     // Check if there are selects that still have the default value
//     var selects = $("#data-selection-container").find("select")
//     if(selects.filter((_, s) => s.selectedIndex == 0).length != 0)
//     {
//         return
//     }

//     $("#pagination-container").removeClass("d-none")
//     clearLinks()

//     $("#show-plot-list-button").removeAttr("disabled")

//     // Read global options
//     readOptionValues()

//     directoryPlotFiles = getFileListForCurrentSelection()
//     await displayPage(page)
//     drawPlotList()
//     drawPageSelector()
//     changeUrlToReflectSettings()
// }

// async function displayPage(page)
// {
//     destroyAllPresentPlots()
//     currentPage = page

//     var numberOfPastPlots = (page - 1) * plotsPerPage
//     var numberOfFuturePlots = directoryPlotFiles.length - numberOfPastPlots
//     var numberOfPlotsToPresent = Math.min(plotsPerPage, numberOfFuturePlots)
    
//     for(var i = 0; i < numberOfPlotsToPresent; i++)
//     {
//         $(`#plot-card-${i}`).removeClass("d-none")

//         var file = directoryPlotFiles[((page - 1) * plotsPerPage) + i]
//         var collection = getCollectionForFile(file)
//         var data = []

//         for(var j = 0; j < collection["files"].length; j++)
//         {
//             var filename = getJustDirname(file) + collection["files"][j] + ".json"
//             var response = await fetch(filename, {
//                 credentials: "same-origin"
//             })
//             var fileData = await response.json()

//             data[j] = fileData[Object.keys(fileData)[0]]
//         }
        
//         var renderTo = `plot-container-${i}`

//         var chartObj = await draw(collection, data, renderTo)
//         chartsObjects.push(chartObj)
//         drawArguments.push([collection, data, renderTo])
//     }

//     for(var i = numberOfPlotsToPresent; i < plotsPerPage; i++)
//     {
//         $(`#plot-card-${i}`).addClass("d-none")
//     }
// }

// function getCollectionForFile(file)
// {
//     var justFilename = getJustFilename(file)
//     var collection = collections.find(x => x["name"] == justFilename)
//     if(collection == undefined)
//     {
//         collection = 
//         {
//             files: [ justFilename ], 
//             name: file, 
//             corr: false
//         }
//     }

//     return collection
// }

// function pageSelected(event, page)
// {
//     event.preventDefault()
//     window.scrollTo(0, 0)

//     displayPage(page)
//     drawPageSelector()
//     addUrlVariable("page", page)
// }

// function drawPlotList()
// {
//     const divStart = `<div class="col-auto mr-2 ml-2 d-inline-block align-top">`
//     const divEnd = `</div></div>`
//     var html = ""
//     var column = ""

//     for(var i = 0; i < directoryPlotFiles.length; i++)
//     {
//         column += `<div class="row">${getJustFilename(directoryPlotFiles[i])}</div>`
//         if((i + 1) % 4 == 0 || i == directoryPlotFiles.length - 1)
//         {
//             var pageNumber = Math.ceil((i + 1) / 4)
//             var pageTitle = `<a class="row small font-italic" href="#" onclick="pageSelected(event, ${pageNumber})">Page ${pageNumber}</a>`
//             html += divStart + pageTitle + column + divEnd
//             column = ""
//         }
//     }

//     if(directoryPlotFiles.length == 0)
//     {
//         html = `<div class="ml-2">No plots found</div>`
//         showAlert("No plots are available for your selection. Please select different data or enter a different search query.")
//     }
//     else
//     {
//         hideAlert()
//     }

//     $("#plot-list-container").html(html)
// }

// function drawPageSelector()
// {
//     var numberOfPages = Math.ceil(directoryPlotFiles.length / plotsPerPage)
//     var html = ""

//     for(var i = 1; i <= numberOfPages; i++)
//     {
//         if(i == currentPage)
//             html += `<li class="page-item active"><a class="page-link">${i}</a></li>`
//         else
//             html += `<li class="page-item"><a class="page-link" href="#" onclick="pageSelected(event, ${i})">${i}</a></li>`
//     }

//     $("#pagination-ul").html(html)
// }

// function updateLinks(parent, run_nr) 
// {
//     var linksInfo = parent.find(".links-info")
//     var omsLink = parent.find(".oms-link")
//     var rrLink = parent.find(".rr-link")

//     linksInfo.text("View run " + run_nr + " in:")
//     omsLink.text("OMS")
//     rrLink.text("RR")
    
//     omsLink.attr("href", "https://cmsoms.cern.ch/cms/runs/report?cms_run=" + run_nr)
//     rrLink.attr("href", "https://cmsrunregistry.web.cern.ch/offline/workspaces/global?run_number=" + run_nr)
// }

// function clearLinks()
// {
//     for(var i = 0; i < plotsPerPage; i++)
//     {
//         var parent = $(`#plot-card-${i}`)

//         var linksInfo = parent.find(".links-info")
//         var omsLink = parent.find(".oms-link")
//         var rrLink = parent.find(".rr-link")

//         linksInfo.text("")
//         omsLink.text("")
//         rrLink.text("")
//         omsLink.attr("href", "")
//         rrLink.attr("href", "")
//     }
// }

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

// function changeUrlToReflectSettings()
// {
//     // Data argument
//     var values = $("#data-selection-container").find("select").map((_, x) => x.value).toArray()
//     addUrlVariable("data", values.join(","))

//     // Filter
//     addUrlVariable("filter", $("#filter-select").val())
//     addUrlVariable("filterValue", getFilterValue())

//     // Options
//     var optionsBitSum = getBitwiseSum()
//     addUrlVariable("options", optionsBitSum)

//     // Search query
//     var searchQuery = $("#search-query-input").val()
//     if(searchQuery == null || searchQuery == "")
//         deleteUrlVariable("search")
//     else
//         addUrlVariable("search", $("#search-query-input").val())

//     // Page
//     addUrlVariable("page", currentPage)
// }

// function destroyAllPresentPlots()
// {
//     chartsObjects.forEach(x => 
//     {
//         try
//         {
//             x.destroy()
//         }
//         catch(error)
//         {
//             console.error(error);
//         }
//     })
//     chartsObjects = []
//     drawArguments = []
// }

// function showAlert(message)
// {
//     $("#alert").html(message)
//     $("#alert").show()
// }

// function hideAlert()
// {
//     $("#alert").html("")
//     $("#alert").hide()
// }

$('#change-ranges-modal').on('hide.bs.modal', function (e)
{
    deleteUrlVariable("modalPlot")
})

const main = (function() {
    return {
        data: {},
        PLOTS_PER_PAGE: 4,
        currentPage: 1,
        chartsObjects: [],
        drawArguments: [],
        
        submitClicked: async function(event) {
            event.preventDefault()
            await this.submit(1)
        },

        submit: async function(page){
            if($("#filter-select").val() == "json") {
                if($("#filter-input-file")[0].files.length == 0)
                    return
            }

            $("#pagination-container").removeClass("d-none")
            this.clearLinks()

            $("#show-plot-list-button").removeAttr("disabled")

            // Read global options
            optionsController.readValues()
            
            $("#submit-button-spinner").show()
            $("#submit-button-title").hide()
            
            let allSeries = {}

            try {
                const url = filterController.getApiUrl()
                const response = await fetch(url, {
                    credentials: "same-origin"
                })
                allSeries = await response.json()
            }
            catch(error) {
                console.error(error);
            }

            $("#submit-button-spinner").hide()
            $("#submit-button-title").show()
            
            // Clear old data
            this.data = {}

            // Get display groups for the selected subsystem
            displayGroups = displayConfig.displayGroups.filter(
                group => group.subsystem === selectionController.selectedSubsystem())
            
            const keysUsedInDisplayGroups = []
            displayGroups.forEach(group => {
                group.series.forEach(series_name => {
                    if(series_name in allSeries) {
                        if(!(group.name in this.data)) {
                            this.data[group.name] = {
                                y_title: group.y_title,
                                plot_title: group.plot_title,
                                correlation: group.correlation,
                                series: []
                            }
                        }

                        this.data[group.name].series.push(allSeries[series_name])
                        keysUsedInDisplayGroups.push(series_name)
                    }
                })
            })
            
            // Collect the remaining series
            const remainingKeys = Object.keys(allSeries).filter(key => !keysUsedInDisplayGroups.includes(key))
            remainingKeys.forEach(key => {
                if(!(key in this.data)) {
                    this.data[key] = {
                        y_title: allSeries[key].metadata.y_title,
                        plot_title: allSeries[key].metadata.plot_title,
                        correlation: false,
                        series: []
                    }
                }
                this.data[key].series.push(allSeries[key])
            })

            // Search
            const searchQuery = optionsController.options.searchQuery
            if(searchQuery !== undefined && searchQuery !== null && searchQuery != "")
            {
                filteredBySearchQuery = {}
                Object.keys(this.data).forEach(key => {
                    if(this.data[key].plot_title.toLowerCase().includes(searchQuery.toLowerCase()))
                    filteredBySearchQuery[key] = this.data[key]
                })
                this.data = filteredBySearchQuery
            }
            
            await this.displayPage(page)
            this.drawPlotList()
            this.drawPageSelector()
            this.changeUrlToReflectSettings()
        },

        displayPage: async function(page){
            this.destroyAllPresentPlots()
            this.currentPage = page

            const numberOfPastPlots = (page - 1) * this.PLOTS_PER_PAGE
            const numberOfFuturePlots = Object.keys(this.data).length - numberOfPastPlots
            const numberOfPlotsToPresent = Math.min(this.PLOTS_PER_PAGE, numberOfFuturePlots)

            for(let i = 0; i < numberOfPlotsToPresent; i++)
            {
                $(`#plot-card-${i}`).removeClass("d-none")

                const key = Object.keys(this.data)[((page - 1) * this.PLOTS_PER_PAGE) + i]
                const plotData = this.data[key]
                const renderTo = `plot-container-${i}`

                const chartObj = await plotter.draw(plotData, renderTo)
                this.chartsObjects.push(chartObj)
                this.drawArguments.push([plotData, renderTo])
            }

            for(let i = numberOfPlotsToPresent; i < this.PLOTS_PER_PAGE; i++)
            {
                $(`#plot-card-${i}`).addClass("d-none")
            }
        },

        pageSelected: function(event, page)
        {
            event.preventDefault()
            window.scrollTo(0, 0)

            this.displayPage(page)
            this.drawPageSelector()
            urlController.set("page", page)
        },

        drawPlotList: function()
        {
            const divStart = `<div class="col-auto mr-2 ml-2 d-inline-block align-top">`
            const divEnd = `</div></div>`
            let html = ""
            let column = ""
            
            Object.keys(this.data).forEach((key, i) => 
            {
                column += `<div class="row">${this.data[key].plot_title}</div>`
                if((i + 1) % 4 == 0 || i == Object.keys(this.data).length - 1)
                {
                    const pageNumber = Math.ceil((i + 1) / 4)
                    const pageTitle = `<a class="row small font-italic" href="#" onclick="main.pageSelected(event, ${pageNumber})">Page ${pageNumber}</a>`
                    html += divStart + pageTitle + column + divEnd
                    column = ""
                }
            })

            if(Object.keys(this.data).length === 0)
            {
                html = `<div class="ml-2">No plots found</div>`
                this.showAlert("No plots are available for your selection. Please select different data or enter a different search query.")
            }
            else
            {
                this.hideAlert()
            }

            $("#plot-list-container").html(html)
        },

        drawPageSelector: function()
        {
            const numberOfPages = Math.ceil(Object.keys(this.data).length / this.PLOTS_PER_PAGE)
            let html = ""

            for(let i = 1; i <= numberOfPages; i++)
            {
                if(i == this.currentPage)
                    html += `<li class="page-item active"><a class="page-link">${i}</a></li>`
                else
                    html += `<li class="page-item"><a class="page-link" href="#" onclick="main.pageSelected(event, ${i})">${i}</a></li>`
            }

            $("#pagination-ul").html(html)
        },

        changeUrlToReflectSettings: function()
        {
            // Data selection argument
            urlController.set("subsystem", $("#subsystem-select").val())
            urlController.set("pl", $("#processing-level-select").val())

            // Filter
            urlController.set("filter", $("#filter-select").val())
            urlController.set("filterValue", filterController.getFilterValue())

            // Options
            const optionsBitSum = optionsController.getBitwiseSum()
            urlController.set("options", optionsBitSum)

            // Search query
            const searchQuery = $("#search-query-input").val()
            if(searchQuery === null || searchQuery === "")
                urlController.delete("search")
            else
                urlController.set("search", $("#search-query-input").val())

            // Page
            urlController.set("page", this.currentPage)
        },

        destroyAllPresentPlots: function()
        {
            this.chartsObjects.forEach(x => 
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
            this.chartsObjects = []
            this.drawArguments = []
        },

        showAlert: function(message)
        {
            $("#alert").html(message)
            $("#alert").show()
        },

        hideAlert: function()
        {
            $("#alert").html("")
            $("#alert").hide()
        },

        updateLinks: function(parent, run_nr) 
        {
            const linksInfo = parent.find(".links-info")
            const omsLink = parent.find(".oms-link")
            const rrLink = parent.find(".rr-link")

            linksInfo.text("View run " + run_nr + " in:")
            omsLink.text("OMS")
            rrLink.text("RR")
            
            omsLink.attr("href", "https://cmsoms.cern.ch/cms/runs/report?cms_run=" + run_nr)
            rrLink.attr("href", "https://cmsrunregistry.web.cern.ch/offline/workspaces/global?run_number=" + run_nr)
        },

        clearLinks: function()
        {
            for(let i = 0; i < this.PLOTS_PER_PAGE; i++)
            {
                const parent = $(`#plot-card-${i}`)

                const linksInfo = parent.find(".links-info")
                const omsLink = parent.find(".oms-link")
                const rrLink = parent.find(".rr-link")

                linksInfo.text("")
                omsLink.text("")
                rrLink.text("")
                omsLink.attr("href", "")
                rrLink.attr("href", "")
            }
        },
    }
}())

$(document).ready(async function()
{
    await selectionController.documentReady()
    filterController.documentReady()
    optionsController.documentReady()

    if(urlController.has("subsystem") && urlController.has("pl"))
    {
        if(urlController.has("page"))
            main.currentPage = urlController.get("page")

        $("#subsystem-select").val(urlController.get("subsystem"))
        $("#processing-level-select").val(urlController.get("pl"))
        
        await main.submit(main.currentPage)
    }

    if(urlController.has("modalPlot"))
    {
        await changeRangesClicked(urlController.get("modalPlot"))
    }
})
