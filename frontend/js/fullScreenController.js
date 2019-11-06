$(document).keyup(function(e) {
    const code = e.keyCode || e.which;
    if(code === 27) {
        const mainModalHidden = $("#gui-main-plot-modal").css("display") === "none"
        const opt1ModalHidden = $("#gui-opt1-plot-modal").css("display") === "none"
        const opt2ModalHidden = $("#gui-opt2-plot-modal").css("display") === "none"

        if(mainModalHidden && opt1ModalHidden && opt2ModalHidden) {
            fullScreenController.exitFullScreen()
        }
    }
    else if(code === 37) {
        if($("#full-screen-content").css("display") !== "none")
            fullScreenController.previousRunClicked()
    }
    else if(code === 39) {
        if($("#full-screen-content").css("display") !== "none")
            fullScreenController.nextRunClicked()
    }
})

const fullScreenController = (function(){
    return {
        isFullScreen: false,
        plotData: undefined,
        chartObject: undefined,
        seriesIndex: 0,
        xIndex: 0,

        enterFullScreen: function(animated=true) {
            const duration = animated ? 300 : 0
            $("#main-content").hide(0)
            $("#full-screen-content").fadeIn(duration)

            this.isFullScreen = true
        },

        exitFullScreen: function() {
            $("#full-screen-content").hide()
            $("#main-content").fadeIn(300)

            urlController.delete("fsPlot")
            $("#fs-gui-plot-image").attr("src", "")
            this.isFullScreen = false
            this.seriesIndex = 0
            this.xIndex = 0
        },

        changeRangesClicked: async function(plotIndex, animated=true)
        {
            this.plotData = main.plotDatas[plotIndex]
            const renderTo = 'fs-plot-container'

            if(this.chartObject !== undefined) {
                try {
                    this.chartObject.destroy()
                }
                catch(error) {
                    console.error(error)
                }
            }

            this.chartObject = await plotter.draw(this.plotData, renderTo)

            const initialStartX = this.plotData.series[0].trends[0].run
            const initialEndX = this.plotData.series[0].trends[this.plotData.series[0].trends.length - 1].run
            const initialStartY = this.chartObject.yAxis[0].min
            const initialEndY = this.chartObject.yAxis[0].max
            $("#start-x").val(initialStartX)
            $("#end-x").val(initialEndX)
            $("#start-y").val(initialStartY)
            $("#end-y").val(initialEndY)

            this.fillRunData()
            this.togglePrevNextButtons()
            this.selectPointInPlot()
            this.enterFullScreen(animated)

            urlController.set("fsPlot", plotIndex)

            this.chartObject.reflow()
        },

        submitClicked: async function()
        {
            const renderTo = 'fs-plot-container'
            const initialStartX = this.plotData.series[0].trends[0].run
            const initialEndX = this.plotData.series[0].trends[this.plotData.series[0].trends.length - 1].run

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
                    const series = this.plotData.series.map(x => x.metadata.name)
                    const base = 'http://vocms0231.cern.ch:8080'
                    const url = `${base}/data?subsystem=${selectionController.selectedSubsystem()}&processing_level=${selectionController.selectedProcessingLevel()}&from_run=${newStartX}&to_run=${newEndX}&series=${series}`
                    const response = await fetch(url, {
                        credentials: "same-origin"
                    })
                    allSeries = await response.json()
                }
                catch(error) {
                    console.error(error)
                }
                $("#modal-submit-button-spinner").hide()

                this.plotData = main.transformAPIResponseToData(allSeries).find(x => x.name == this.plotData.name)
                if(this.chartObject !== undefined) {
                    try {
                        this.chartObject.destroy()
                    }
                    catch(error) {
                        console.error(error)
                    }
                }
                this.chartObject = await plotter.draw(this.plotData, renderTo)
            }
            
            this.chartObject.yAxis[0].update(
            {
                min: newStartY,
                max: newEndY
            })

            $("#start-y").val(this.chartObject.yAxis[0].min)
            $("#end-y").val(this.chartObject.yAxis[0].max)
        },

        selectDataPoint: function(seriesIndex, xIndex) {
            this.seriesIndex = seriesIndex
            this.xIndex = xIndex
            this.fillRunData()
            this.togglePrevNextButtons()
        },

        fillRunData: function() 
        {
            const dataPoint = this.plotData.series[this.seriesIndex].trends[this.xIndex]

            $("#fs-value-series").html(String(this.plotData.series[this.seriesIndex].metadata.y_title))
            $("#fs-value-value").html(String(dataPoint.value))
            $("#fs-value-error").html(String(dataPoint.error))
			$("#fs-value-run").html(String(dataPoint.run))
			$("#fs-value-fill").html(String(dataPoint.oms_info.fill_number))
			$("#fs-value-duration").html(String(dataPoint.oms_info.duration))
			$("#fs-value-delivered-lumi").html(String(dataPoint.oms_info.delivered_lumi))
			$("#fs-value-b-field").html(String(dataPoint.oms_info.b_field))
			$("#fs-value-end-lumi").html(String(dataPoint.oms_info.end_lumi))
			$("#fs-value-start-time").html(String(dataPoint.oms_info.start_time).replace("T", " ").replace("Z", ""))
			$("#fs-value-end-time").html(String(dataPoint.oms_info.end_time).replace("T", " ").replace("Z", ""))
			$("#fs-value-energy").html(String(dataPoint.oms_info.energy))
			$("#fs-value-era").html(String(dataPoint.oms_info.era))
			$("#fs-value-injection-scheme").html(String(dataPoint.oms_info.injection_scheme))
			$("#fs-value-hlt-key").html(String(dataPoint.oms_info.hlt_key))
			$("#fs-value-hlt-physics-rate").html(String(dataPoint.oms_info.hlt_physics_rate))
			$("#fs-value-l1t-key").html(String(dataPoint.oms_info.l1_key))
			$("#fs-value-l1t-rate").html(String(dataPoint.oms_info.l1_rate))
            $("#fs-value-recorded-lumi").html(String(dataPoint.oms_info.recorded_lumi))

            $("#fs-value-oms-url").attr("href", `https://cmsoms.cern.ch/cms/runs/report?cms_run=${dataPoint.run}`)
            $("#fs-value-gui-url").attr("href", String(dataPoint.main_gui_url))
            $("#fs-value-rr-url").attr("href", `https://cmsrunregistry.web.cern.ch/offline/workspaces/global?run_number=${dataPoint.run}`)
            
            $(".fs-run").html(String(dataPoint.run))
            $("#fs-gui-main-plot-image").attr("src", dataPoint.main_image_url)
            $("#fs-gui-opt1-plot-image").attr("src", dataPoint.optional1_image_url)
            $("#fs-gui-opt2-plot-image").attr("src", dataPoint.optional2_image_url)
            
            $("#main-plot-gui-url").attr("href", `https://cmsrunregistry.web.cern.ch/offline/workspaces/global?run_number=${dataPoint.main_gui_url}`)
            $("#opt1-plot-gui-url").attr("href", `https://cmsrunregistry.web.cern.ch/offline/workspaces/global?run_number=${dataPoint.opt1_gui_url}`)
            $("#opt2-plot-gui-url").attr("href", `https://cmsrunregistry.web.cern.ch/offline/workspaces/global?run_number=${dataPoint.opt2_gui_url}`)

            $("#gui-main-plot-modal-image").attr("src", dataPoint.main_image_url)
            $("#gui-opt1-plot-modal-image").attr("src", dataPoint.optional1_image_url)
            $("#gui-opt2-plot-modal-image").attr("src", dataPoint.optional2_image_url)
            
            $("#gui-main-plot-modal-path").text(this.plotData.series[this.seriesIndex].metadata.main_me_path)
            $("#gui-opt1-plot-modal-path").text(this.plotData.series[this.seriesIndex].metadata.optional1_me_path)
            $("#gui-opt2-plot-modal-path").text(this.plotData.series[this.seriesIndex].metadata.optional2_me_path)

            $("#gui-plot-modal-run").text(dataPoint.run)

            if(this.plotData.series[this.seriesIndex].metadata.optional1_me_path === null) {
                $("#opt1-plot-container").hide()
            }
            else {
                $("#opt1-plot-container").show()
            }

            if(this.plotData.series[this.seriesIndex].metadata.optional2_me_path === null) {
                $("#opt2-plot-container").hide()
            }
            else {
                $("#opt2-plot-container").show()
            }
        },

        nextRunClicked: function() {
            if(this.xIndex >= this.plotData.series[this.seriesIndex].trends.length - 1)
                return
            
            this.xIndex++
            this.fillRunData()
            this.togglePrevNextButtons()
            this.selectPointInPlot()
        },

        previousRunClicked: function() {
            if(this.xIndex <= 0)
                return

            this.xIndex--
            this.fillRunData()
            this.togglePrevNextButtons()
            this.selectPointInPlot()
        },

        togglePrevNextButtons: function() {
            if(this.xIndex >= this.plotData.series[this.seriesIndex].trends.length - 1)
                $("#fs-next-btn").addClass('disabled')
            else
                $("#fs-next-btn").removeClass('disabled')
            if(this.xIndex <= 0)
                $("#fs-prev-btn").addClass('disabled')
            else
                $("#fs-prev-btn").removeClass('disabled')
        },

        selectPointInPlot: function() {
            const series = this.chartObject.series.find(x => x.name === this.plotData.series[this.seriesIndex].metadata.y_title)
            if(series !== undefined)
                series.data[this.xIndex].select()
        },

        documentReady: function() {
            
        }
    }
}())
