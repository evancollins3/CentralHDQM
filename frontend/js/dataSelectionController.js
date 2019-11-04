
const selectionController = (function() {
    return {
        dataIndex: {},
        setupSelects: function(dataIndex) {
            this.dataIndex = dataIndex
            const select = document.getElementById("subsystem-select")
            
            const option = document.createElement("option")
            option.text = "Select a subsystem"
            option.disabled = true
            select.add(option)

            this.dataIndex.forEach(element => {
                const option = document.createElement("option")
                option.text = element.subsystem
                select.add(option)
            })
            this.selectionChanged(select)
        },

        selectionChanged: function(select1) {
            const item = this.dataIndex.find(element => element.subsystem === select1.value)
            
            $("#processing-level-select").empty()
            const select2 = document.getElementById("processing-level-select")

            const option = document.createElement("option")
            option.text = "Select processing level"
            option.disabled = true
            select2.add(option)

            item.processing_levels.forEach(element => {
                const option = document.createElement("option")
                option.text = element
                select2.add(option)
            })
        },

        selectedSubsystem() { return document.getElementById("subsystem-select").value },
        selectedProcessingLevel() { return document.getElementById("processing-level-select").value },

        documentReady: async function() {
            try {
                const response = await fetch("http://vocms0231.cern.ch:8080/subsystems", {
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
