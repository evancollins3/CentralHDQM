
const selectionController = (function() {
    return {
        selectedSubsystem() { return document.getElementById("subsystem-select").value },
        selectedPD() { return document.getElementById("pd-select").value },
        selectedProcessingString() { return document.getElementById("processing-string-select").value },

        isSubsystemSelected() { return document.getElementById("subsystem-select").selectedIndex !== 0 },
        isPDSelected() { return document.getElementById("pd-select").selectedIndex !== 0 },
        isProcessingStringSelected() { return document.getElementById("processing-string-select").selectedIndex !== 0 },

        documentReady: async function() {
            try {
                const base = config.getBaseAPIUrl()
                const response = await fetch(`${base}/selection`, {
                    credentials: "same-origin"
                })
                const dataIndex = await response.json()
                
                selectComponent.register(
                    ['#subsystem-select', '#pd-select', '#processing-string-select'], 
                    dataIndex, 
                    ['Select a subsystem', 'Select a primary dataset', 'Select a processing string'])
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
