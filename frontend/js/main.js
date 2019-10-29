
$('#change-ranges-modal').on('hide.bs.modal', function (e)
{
    urlController.delete("modalPlot")
})

$('#gui-plot-modal').on('show.bs.modal', function (e) 
{
    $('#change-ranges-modal').css('z-index', 1000)
})

$('#gui-plot-modal').on('hide.bs.modal', function (e) 
{
    $('#change-ranges-modal').css('z-index', 1050)
})

const main = (function() {
    return {
        data: {},
        PLOTS_PER_PAGE: 4,
        currentPage: 1,
        chartsObjects: [],
        modal: {
            plotDatas: [],
            popupChartObject: undefined,
            plotIndex: 0,
        },
        
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
                const url = await filterController.getApiUrl()
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
            
            this.data = this.transformAPIResponseToData(allSeries)

            // Search
            const searchQuery = optionsController.options.searchQuery
            if(searchQuery !== undefined && searchQuery !== null && searchQuery != "")
            {
                filteredBySearchQuery = []
                this.data.forEach(plotData => {
                    if(plotData.plot_title.toLowerCase().includes(searchQuery.toLowerCase()))
                    filteredBySearchQuery.push(plotData)
                })
                this.data = filteredBySearchQuery
            }
            
            await this.displayPage(page)
            this.drawPlotList()
            this.drawPageSelector()
            this.changeUrlToReflectSettings()
        },

        transformAPIResponseToData: function(allSeries) {
            const data = []
            const allSeriesNames = allSeries.map(x => x.metadata.name)

            // Get display groups for the selected subsystem
            const displayGroups = displayConfig.displayGroups.filter(
                group => group.subsystem === selectionController.selectedSubsystem())

            const namesUsedInDisplayGroups = []
            displayGroups.forEach(group => {
                const plotData = {
                    plot_title: group.plot_title,
                    y_title: group.y_title,
                    name: group.name,
                    correlation: group.correlation,
                    series: []
                }

                group.series.forEach(seriesName => {
                    if(allSeriesNames.includes(seriesName)) {
                        plotData.series.push(allSeries.find(x => x.metadata.name == seriesName))
                        namesUsedInDisplayGroups.push(seriesName)
                    }
                })

                if(plotData.series.length !== 0)
                    data.push(plotData)
            })

            // Collect the remaining series
            allSeries.forEach(series => {
                if(!namesUsedInDisplayGroups.includes(series.metadata.name)) {
                    const plotData = {
                        plot_title: series.metadata.plot_title,
                        y_title: series.metadata.y_title,
                        name: series.metadata.name,
                        correlation: false,
                        series: [series]
                    }
                    data.push(plotData)
                }
            })

            return data
        },

        displayPage: async function(page){
            this.destroyAllPresentPlots()
            this.currentPage = page

            const numberOfPastPlots = (page - 1) * this.PLOTS_PER_PAGE
            const numberOfFuturePlots = this.data.length - numberOfPastPlots
            const numberOfPlotsToPresent = Math.min(this.PLOTS_PER_PAGE, numberOfFuturePlots)

            for(let i = 0; i < numberOfPlotsToPresent; i++)
            {
                $(`#plot-card-${i}`).removeClass("d-none")

                const plotData = this.data[((page - 1) * this.PLOTS_PER_PAGE) + i]
                const renderTo = `plot-container-${i}`

                const chartObj = await plotter.draw(plotData, renderTo)
                this.chartsObjects.push(chartObj)
                this.modal.plotDatas.push(plotData)
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
            
            this.data.forEach((plotData, i) => 
            {
                column += `<div class="row">${plotData.plot_title}</div>`
                if((i + 1) % 4 == 0 || i == plotData.length - 1)
                {
                    const pageNumber = Math.ceil((i + 1) / 4)
                    const pageTitle = `<a class="row small font-italic" href="#" onclick="main.pageSelected(event, ${pageNumber})">Page ${pageNumber}</a>`
                    html += divStart + pageTitle + column + divEnd
                    column = ""
                }
            })

            if(this.data.length === 0)
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
            const numberOfPages = Math.ceil(this.data.length / this.PLOTS_PER_PAGE)
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

        changeRangesClicked: async function(plotIndex)
        {
            this.modal.plotIndex = plotIndex
            const plotData = this.modal.plotDatas[plotIndex]
            const renderTo = 'change-ranges-container'

            if(this.modal.popupChartObject !== undefined)
                this.modal.popupChartObject.destroy()

            this.modal.popupChartObject = await plotter.draw(plotData, renderTo)

            const initialStartX = plotData.series[0].trends[0].run
            const initialEndX = plotData.series[0].trends[plotData.series[0].trends.length - 1].run
            const initialStartY = this.modal.popupChartObject.yAxis[0].min
            const initialEndY = this.modal.popupChartObject.yAxis[0].max
            $("#start-x").val(initialStartX)
            $("#end-x").val(initialEndX)
            $("#start-y").val(initialStartY)
            $("#end-y").val(initialEndY)

            $('#change-ranges-modal').modal('show')

            urlController.set("modalPlot", plotIndex)
        },

        popupSubmitClicked: async function()
        {
            let plotData = this.modal.plotDatas[this.modal.plotIndex]
            const renderTo = 'change-ranges-container'
            const initialStartX = plotData.series[0].trends[0].run
            const initialEndX = plotData.series[0].trends[plotData.series[0].trends.length - 1].run

            const newStartX = parseInt($("#start-x").val())
            const newEndX = parseInt($("#end-x").val())
            const newStartY = $("#start-y").val()
            const newEndY = $("#end-y").val()

            if(newStartX !== initialStartX || newEndX !== initialEndX)
            {
                // X range changed, fetch new data!
                let allSeries = []
                try {
                    $("#modal-submit-button-spinner").show()
                    const series = plotData.series.map(x => x.metadata.name)
                    const base = 'http://vocms0231.cern.ch:8080'
                    const url = `${base}/data?subsystem=${selectionController.selectedSubsystem()}&processing_level=${selectionController.selectedProcessingLevel()}&from_run=${newStartX}&to_run=${newEndX}&series=${series}`
                    const response = await fetch(url, {
                        credentials: "same-origin"
                    })
                    allSeries = await response.json()
                }
                catch(error) {
                    console.error(error);
                }
                $("#modal-submit-button-spinner").hide()

                plotData = this.transformAPIResponseToData(allSeries).find(x => x.name == plotData.name)
                if(this.modal.popupChartObject !== undefined)
                    this.modal.popupChartObject.destroy()
                this.modal.popupChartObject = await plotter.draw(plotData, renderTo)
            }
            
            this.modal.popupChartObject.yAxis[0].update(
            {
                min: newStartY,
                max: newEndY
            })

            $("#start-y").val(this.modal.popupChartObject.yAxis[0].min)
            $("#end-y").val(this.modal.popupChartObject.yAxis[0].max)
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
            this.modal.plotDatas = []
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

        updateLinks: function(parent, plotData, run, seriesIndex) 
        {
            const dataPoint = plotData.series[seriesIndex].trends.find(x => x.run === run)

            const linksInfo = parent.find(".links-info")
            const omsLink = parent.find(".oms-link")
            const rrLink = parent.find(".rr-link")
            const guiLink = parent.find(".gui-link")
            const imgLink = parent.find(".img-link")

            linksInfo.text("Run " + dataPoint.run + ":")
            omsLink.text("OMS")
            rrLink.text("RR")
            guiLink.text("GUI")
            imgLink.text("IMG")
            
            omsLink.attr("href", "https://cmsoms.cern.ch/cms/runs/report?cms_run=" + dataPoint.run)
            rrLink.attr("href", "https://cmsrunregistry.web.cern.ch/offline/workspaces/global?run_number=" + dataPoint.run)
            guiLink.attr("href", dataPoint.gui_url)

            $("#gui-plot-modal-image").attr("src", dataPoint.image_url)
            $("#gui-plot-modal-run").text(dataPoint.run)
            $("#gui-plot-modal-path").text(plotData.series[seriesIndex].metadata.me_path)
        },

        clearLinks: function()
        {
            for(let i = 0; i < this.PLOTS_PER_PAGE; i++)
            {
                const parent = $(`#plot-card-${i}`)

                const linksInfo = parent.find(".links-info")
                const omsLink = parent.find(".oms-link")
                const rrLink = parent.find(".rr-link")
                const guiLink = parent.find(".gui-link")
                const imgLink = parent.find(".img-link")

                linksInfo.text("")
                omsLink.text("")
                rrLink.text("")
                guiLink.text("")
                imgLink.text("")
                omsLink.attr("href", "")
                rrLink.attr("href", "")
                guiLink.attr("href", "")
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
        await main.changeRangesClicked(urlController.get("modalPlot"))
    }
})
