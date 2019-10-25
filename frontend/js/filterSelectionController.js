
const filterController = (function(){
    return {
        filterSelectionChanged: function()
        {
            const value = $("#filter-select").val()
            const container = $("#filter-value-container")

            if(value == "latest")
            {
                container.html(`<div class="">
                    <input type="number" class="form-control form-control-sm" id="filter-input-latest" value="50" placeholder="Number of latest runs">
                </div>`)
            }
            else if(value == "range")
            {
                container.html(`<div class="row">
                <div class="col-6">
                <input type="number" class="form-control form-control-sm" id="filter-input-range-low" value="322348" placeholder="From">
                </div>
                <div class="col-6">
                    <input type="number" class="form-control form-control-sm" id="filter-input-range-high" value="325310" placeholder="To">
                </div>
                </div>`)
            }
            else if(value == "list")
            {
                container.html(`<div class="">
                    <input type="text" class="form-control form-control-sm" id="filter-input-list" value="325308, 325309, 325310" placeholder="Comma separated list of run numbers">
                </div>`)
            }
            else if(value == "json")
            {
                container.html(`<div class="">
                    <input type="file" class="form-control form-control-sm form-control-file" id="filter-input-file" style="padding-top: 2px;">
                </div>`)
            }
            else if(value == "rr")
            {
                container.html(`<div class="">
                    <input type="text" class="form-control form-control-sm" id="filter-input-rr" placeholder="https://cmsrunregistry.web.cern.ch/online/runs/all">
                </div>`)
            }
        },

        getFilterValue: function()
        {
            const value = $("#filter-select").val()

            if(value == "latest")
            {
                return $("#filter-input-latest").val()
            }
            else if(value == "range")
            {
                return `${$("#filter-input-range-low").val()},${$("#filter-input-range-high").val()}`
            }
            else if(value == "list")
            {
                return $("#filter-input-list").val()
            }
            else if(value == "json")
            {
                // Would be possible to return the contents of a file but for now this is unsupported
                return ""
            }
            else if(value == "rr")
            {
                return $("#filter-input-rr").val()
            }
        },

        setFilterValue: function(filterValue)
        {
            const value = $("#filter-select").val()

            if(value == "latest")
            {
                $("#filter-input-latest").val(filterValue)
            }
            else if(value == "range")
            {
                const highLow = filterValue.split(",")
                $("#filter-input-range-low").val(highLow[0])
                $("#filter-input-range-high").val(highLow[1])
            }
            else if(value == "list")
            {
                $("#filter-input-list").val(filterValue)
            }
            else if(value == "json")
            {
                // For now this is unsupported
            }
            else if(value == "rr")
            {
                $("#filter-input-rr").val(filterValue)
            }
        },

        getApiUrl: function()
        {
            `http://vocms0231.cern.ch:8080/data?subsystem=${selectionController.selectedSubsystem()}&processing_level=${selectionController.selectedProcessingLevel()}&from_run=319654&to_run=319690`
            const base = 'http://vocms0231.cern.ch:8080'

            const value = $("#filter-select").val()

            if(value == "latest")
            {
                return `${base}/data?subsystem=${selectionController.selectedSubsystem()}&processing_level=${selectionController.selectedProcessingLevel()}&latest=${$("#filter-input-latest").val()}`
            }
            else if(value == "range")
            {
                return `${base}/data?subsystem=${selectionController.selectedSubsystem()}&processing_level=${selectionController.selectedProcessingLevel()}&from_run=${$("#filter-input-range-low").val()}&to_run=${$("#filter-input-range-high").val()}`
            }
            else if(value == "list")
            {
                // return $("#filter-input-list").val()
                return `${base}/data?subsystem=${selectionController.selectedSubsystem()}&processing_level=${selectionController.selectedProcessingLevel()}&runs=${$("#filter-input-list").val()}`
            }
            else if(value == "json")
            {
                // TODO: make this work!
                return `${base}/data?subsystem=${selectionController.selectedSubsystem()}&processing_level=${selectionController.selectedProcessingLevel()}}`
            }
            else if(value == "rr")
            {
                return `${base}/data?subsystem=${selectionController.selectedSubsystem()}&processing_level=${selectionController.selectedProcessingLevel()}}`
            }
        },

        documentReady: function() {
            // Interpret url variables
            const filter = urlController.get("filter")
            if(filter != null)
                $("#filter-select").val(filter)
            
            this.filterSelectionChanged()

            const filterValue = urlController.get("filterValue")
            if(filter != null && filterValue != null)
                this.setFilterValue(urlController.get("filterValue"))

            $("#search-query-input").val(urlController.get("search"))
        }
    }
}())
