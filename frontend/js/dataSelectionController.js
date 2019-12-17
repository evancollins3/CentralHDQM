
const selectionController = (function() {
    return {
        dataIndex: {},
        setupSelects: function(dataIndex) {
            this.dataIndex = dataIndex

            const subsystemSelect = document.getElementById("subsystem-select")
            const placeholder = document.createElement("option")
            placeholder.text = "Select a subsystem"
            placeholder.disabled = true
            placeholder.selected = true
            subsystemSelect.add(placeholder)

            Object.keys(this.dataIndex).forEach(element => {
                const option = document.createElement("option")
                option.text = element
                subsystemSelect.add(option)
            })
    
        },

        subsystemChanged: function() {
            const subsystem = this.selectedSubsystem()
            const pdSelect = document.getElementById("pd-select")
            $("#pd-select").empty()

            const placeholder = document.createElement("option")
            placeholder.text = "Select a primary dataset"
            placeholder.disabled = true
            placeholder.selected = true
            pdSelect.add(placeholder)
            
            const elements = this.dataIndex[subsystem]
            if(elements !== undefined) {
                Object.keys(elements).forEach(element => {
                    const option = document.createElement("option")
                    option.text = element
                    pdSelect.add(option)
                })
            }

            this.pdChanged()
        },

        pdChanged: function() {
            const subsystem = this.selectedSubsystem()
            const pd = this.selectedPD()
            const processingStringSelect = document.getElementById("processing-string-select")
            $("#processing-string-select").empty()

            const placeholder = document.createElement("option")
            placeholder.text = "Select a processing string"
            placeholder.disabled = true
            placeholder.selected = true
            processingStringSelect.add(placeholder)

            const elements = this.dataIndex[subsystem][pd]
            if(elements !== undefined) {
                elements.forEach(element => {
                    const option = document.createElement("option")
                    option.text = element
                    processingStringSelect.add(option)
                })
            }
        },

        selectedSubsystem() { return document.getElementById("subsystem-select").value },
        selectedPD() { return document.getElementById("pd-select").value },
        selectedProcessingString() { return document.getElementById("processing-string-select").value },

        documentReady: async function() {
            try {
                const base = config.getBaseAPIUrl()
                const response = await fetch(`${base}/selection`, {
                    credentials: "same-origin"
                })
                dataIndex = await response.json()
                selectionController.setupSelects(dataIndex)
            }
            catch(error) {
                console.error(error)
                main.showAlert("There was an error loading the data from the server. Please try again later.")
            }

            // Safe to click submit now
            $("#submit-button").removeAttr("disabled")
            $("#submit-button-spinner").hide()
            $("#submit-button-title").show()
        }
    }
}())
