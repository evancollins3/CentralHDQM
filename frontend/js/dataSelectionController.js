
const selectionController = (function() {
    return {
        dataIndex: {},
        setupSelects: function(dataIndex) {
            this.dataIndex = dataIndex

            const subsystemSelect = document.getElementById("subsystem-select")
            const pdSelect = document.getElementById("pd-select")
            const processingStringSelect = document.getElementById("processing-string-select")

            const option1 = document.createElement("option")
            option1.text = "Select a subsystem"
            option1.disabled = true
            subsystemSelect.add(option1)

            option2 = document.createElement("option")
            option2.text = "Select a primary dataset"
            option2.disabled = true
            pdSelect.add(option2)

            option3 = document.createElement("option")
            option3.text = "Select a processing string"
            option3.disabled = true
            processingStringSelect.add(option3)

            this.dataIndex.subsystems.forEach(element => {
                const option = document.createElement("option")
                option.text = element
                subsystemSelect.add(option)
            })

            this.dataIndex.pds.forEach(element => {
                const option = document.createElement("option")
                option.text = element
                pdSelect.add(option)
            })

            this.dataIndex.processing_strings.forEach(element => {
                const option = document.createElement("option")
                option.text = element
                processingStringSelect.add(option)
            })
        },

        selectedSubsystem() { return document.getElementById("subsystem-select").value },
        selectedPD() { return document.getElementById("pd-select").value },
        selectedProcessingString() { return document.getElementById("processing-string-select").value },

        documentReady: async function() {
            try {
                const base = config.getAPIUrl()
                const response = await fetch(`${base}/subsystems`, {
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
