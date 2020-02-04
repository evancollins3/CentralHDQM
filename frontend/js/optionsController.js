
const optionsController = (function(){
    return {
        options:
        {
            showErrors: false,
            showFills: true,
            showDurations: true,
            showRegression: true,
            showXRange: false,
            showIntLumi: false,
            showDatetime: false,
            searchQuery: "",
        },

        readValues: function()
        {
            this.options.showErrors = $("#option-show-errors").prop("checked")
            this.options.showFills = $("#option-show-fills").prop("checked")
            this.options.showDurations = $("#option-show-run-duration").prop("checked")
            this.options.showRegression = $("#option-show-regression-lines").prop("checked")
            this.options.showXRange = $("#option-show-xrange").prop("checked")
            this.options.showIntLumi = $("#option-show-int-lumi").prop("checked")
            this.options.showDatetime = $("#option-show-datetime").prop("checked")
            this.options.searchQuery = $("#search-query-input").val()
        },

        optionToggled: function(element)
        {
            // Relative selects
            if(element.value === "option5" && element.checked)
            {
                $("#option-show-int-lumi").prop("checked", false)
                $("#option-show-datetime").prop("checked", false)
            }
            else if(element.value === "option6" && element.checked)
            {
                $("#option-show-xrange").prop("checked", false)
                $("#option-show-datetime").prop("checked", false)
            }
            else if(element.value === "option7" && element.checked)
            {
                $("#option-show-int-lumi").prop("checked", false)
                $("#option-show-xrange").prop("checked", false)
            }

            // When run duration XRange is selected, run durations option doesn't make sense
            if($("#option-show-xrange").prop("checked"))
            {
                $("#option-show-run-duration").prop("checked", true)
                $("#option-show-run-duration").prop("disabled", true)
            }
            else
            {
                $("#option-show-run-duration").prop("disabled", false)
            }
        },

        updateUI: function()
        {
            $("#option-show-errors").prop("checked", this.options.showErrors)
            $("#option-show-fills").prop("checked", this.options.showFills)
            $("#option-show-run-duration").prop("checked", this.options.showDurations)
            $("#option-show-regression-lines").prop("checked", this.options.showRegression)
            $("#option-show-xrange").prop("checked", this.options.showXRange)
            $("#option-show-int-lumi").prop("checked", this.options.showIntLumi)
            $("#option-show-datetime").prop("checked", this.options.showDatetime)

            // When run duration XRange is selected, run durations option doesn't make sense
            if($("#option-show-xrange").prop("checked"))
            {
                $("#option-show-run-duration").prop("checked", true)
                $("#option-show-run-duration").prop("disabled", true)
            }
            else
            {
                $("#option-show-run-duration").prop("disabled", false)
            }
        },

        getBitwiseSum: function()
        {
            const showErrors = this.options.showErrors = $("#option-show-errors").prop("checked") << 0
            const showFills = this.options.showFills = $("#option-show-fills").prop("checked") << 1
            const showDurations = this.options.showDurations = $("#option-show-run-duration").prop("checked") << 2
            const showRegression = this.options.showRegression = $("#option-show-regression-lines").prop("checked") << 3
            const showXRange = this.options.showXRange = $("#option-show-xrange").prop("checked") << 4
            const showIntLumi = this.options.showIntLumi = $("#option-show-int-lumi").prop("checked") << 5
            const showDatetime = this.options.showDatetime = $("#option-show-datetime").prop("checked") << 6

            return showErrors + showFills + showDurations + showRegression + showXRange + showIntLumi + showDatetime
        },

        setFromBitwiseSum: function(sum)
        {
            this.options.showErrors = this.isBitSet(sum, 0)
            this.options.showFills = this.isBitSet(sum, 1)
            this.options.showDurations = this.isBitSet(sum, 2)
            this.options.showRegression = this.isBitSet(sum, 3)
            this.options.showXRange = this.isBitSet(sum, 4)
            this.options.showIntLumi = this.isBitSet(sum, 5)
            this.options.showDatetime = this.isBitSet(sum, 6)
        },

        isBitSet: function(value, bit)
        {
            const mask = 1 << bit
            return (value & mask) != 0
        },

        documentReady: function() {
            if(urlController.has("options"))
            {
                const optionsBitSum = urlController.get("options")
                this.setFromBitwiseSum(optionsBitSum)
                this.updateUI()
            }
        }
    }
}())
