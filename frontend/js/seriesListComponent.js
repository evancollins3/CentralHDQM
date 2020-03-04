
const seriesListComponent = (function() {
    return {
        dataIndexLoaded: false,
        maxId: 0,
        series: [],

        enterFullScreen: async function()
        {
            if(!this.dataIndexLoaded)
            {
                try {
                    const base = config.getBaseAPIUrl()
                    const response = await fetch(`${base}/plot_selection`, {
                        credentials: "same-origin"
                    })
                    const plotDataIndex = await response.json()

                    selectComponent.register(
                        ['#fs-subsystem-select', '#fs-pd-select', '#fs-processing-string-select', '#fs-plot-select'], 
                        plotDataIndex, 
                        ['Select a subsystem', 'Select a primary dataset', 'Select a processing string', 'Select a plot'])
                    
                    this.dataIndexLoaded = true
                }
                catch(error) {
                    console.error(error)
                }
            }
            
            $("#fs-subsystem-select").val(selectionController.selectedSubsystem()).trigger('change')
            $("#fs-pd-select").val(selectionController.selectedPD()).trigger('change')
            $("#fs-processing-string-select").val(selectionController.selectedProcessingString()).trigger('change')
        },

        setup: function(series) {
            this.maxId = 0
            this.series = []

            $("#fs-series-list-container").empty()
            series.forEach(element => {
                this.addNewSeries(selectionController.selectedSubsystem(), selectionController.selectedPD(), selectionController.selectedProcessingString(), element.metadata.plot_title)
            })
        },

        addNewSeries: async function(subsystem, pd, ps, name, animated = false, series_id = undefined) {
            const id = subsystem + pd + ps + name

            // Check if this series does not exist yet
            if(this.series.filter(x => x.id === id && x.removed === false).length > 0)
                return

            // Add series to the plot
            if(series_id !== undefined)
            {
                const runFrom = fullScreenController.plotData.series[0].trends[0].run
                const runTo = fullScreenController.plotData.series[0].trends[fullScreenController.plotData.series[0].trends.length - 1].run

                let allSeries = []
                try {
                    this.showSpinner()
                    const base = config.getBaseAPIUrl()
                    const url = `${base}/data?series_id=${series_id}&from_run=${runFrom}&to_run=${runTo}`
                    const response = await fetch(url, {
                        credentials: "same-origin"
                    })
                    allSeries = await response.json()
                }
                catch(error) {
                    console.error(error)
                    this.showError("Unable to get the series data from the API")
                    return
                }
                finally {
                    this.hideSpinner()
                }

                if(allSeries.length == 0)
                {
                    this.showError("The selected series doesn't exist for the selected runs")
                    return
                }
            
                fullScreenController.plotData.series.push(allSeries[0])
                await fullScreenController.redrawPlot()
            }

            // Add series to a list in this component
            const index = this.maxId++
            this.series[index] = {}
            this.series[index].id = id
            this.series[index].subsystem = subsystem
            this.series[index].name = name
            this.series[index].removed = false

            $("#fs-series-list-container").append(`
            <li class="list-group-item" id="fs-series-list-item-${index}">
				<div class="row">
					<div class="col mb-0">
						<small>${subsystem}/${pd}/${ps}</small></br>
						${name}
					</div>
					<div class="col-auto pr-1 mt-auto mb-auto">
						<button class="btn btn-sm btn-outline-danger" onclick="seriesListComponent.removeClicked(${index})">Remove</button>
					</div>
				</div>
			</li>
            `)

            if(animated === true) 
            {
                $(`#fs-series-list-item-${index}`).hide(0)
                $(`#fs-series-list-item-${index}`).slideDown("fast")
            }

            this.toggleCorrelationCheckboxIfNeeded()
            this.hideError()
        },

        removeSeries: async function(index) {
            // We can't remove last trend
            if(fullScreenController.plotData.series.length == 1)
                return
            
            // Remove from plot data that will be used to redraw the plot
            const toRemoveIndex = fullScreenController.plotData.series.findIndex(x => x.metadata.name === this.series[index].name)
            if (toRemoveIndex > -1)
                fullScreenController.plotData.series.splice(toRemoveIndex, 1)

            await fullScreenController.redrawPlot()
            
            // Update UI
            const target = $(`#fs-series-list-item-${index}`)
            target.slideUp("fast", function() { 
                target.remove() 
            })

            this.series[index].removed = true
            this.toggleCorrelationCheckboxIfNeeded()
        },

        toggleCorrelationCheckboxIfNeeded: function() {
            if(this.series.filter(x => x.removed === false).length == 2)
            {
                $("#fs-correlation-checkbox").prop("disabled", false)
            }
            else
            {
                $("#fs-correlation-checkbox").prop("disabled", true)
                $("#fs-correlation-checkbox").prop("checked", false)
                $('#fs-correlation-checkbox').trigger('change')
            }
        },

        addClicked: async function () {
            // Check if value is selected
            if(!$("#fs-plot-select option:selected").is("[disabled]"))
            {
                await this.addNewSeries($("#fs-subsystem-select").val(), $("#fs-pd-select").val(), 
                    $("#fs-processing-string-select").val(), $("#fs-plot-select option:selected").text(), 
                    true, parseInt($("#fs-plot-select option:selected").val()))
            }
        },

        removeClicked: function (index) {
            this.removeSeries(index)
        },

        showError: function(error) {
            $("#fs-add-series-error").text(error)
            $("#fs-add-series-error").slideDown()
        },

        hideError: function() {
            $("#fs-add-series-error").slideUp()
        },

        showSpinner: function() {
            $("#fs-add-series-button-spinner").show()
            $("#fs-add-series-button-text").hide()
        },

        hideSpinner: function() {
            $("#fs-add-series-button-spinner").hide()
            $("#fs-add-series-button-text").show()
        },

        documentReady: function() {
            $('#fs-series-collapse').on('show.bs.collapse', function () {
                $("#fs-series-collapse-show-icon").hide()
                $("#fs-series-collapse-hide-icon").show()
            })

            $('#fs-series-collapse').on('hide.bs.collapse', function () {
                $("#fs-series-collapse-show-icon").show()
                $("#fs-series-collapse-hide-icon").hide()
            })

            $('#fs-correlation-checkbox').change(async function() {
                if(fullScreenController.plotData.correlation !== this.checked)
                {
                    fullScreenController.plotData.correlation = this.checked
                    await fullScreenController.redrawPlot()
                }
            });
        }
    }
}())
