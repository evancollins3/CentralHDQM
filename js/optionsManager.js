
var globalOptions = 
{
    showErrors: false,
    showFills: true,
    showDurations: true,
    showRegression: true,
    showXRange: false,
    showIntLumi: false,
    showDatetime: false,
}

function readCheckboxOptionValues()
{
    globalOptions.showErrors = $("#option-show-errors").prop("checked")
    globalOptions.showFills = $("#option-show-fills").prop("checked")
    globalOptions.showDurations = $("#option-show-run-duration").prop("checked")
    globalOptions.showRegression = $("#option-show-regression-lines").prop("checked")
    globalOptions.showXRange = $("#option-show-xrange").prop("checked")
    globalOptions.showIntLumi = $("#option-show-int-lumi").prop("checked")
    globalOptions.showDatetime = $("#option-show-datetime").prop("checked")
}

function optionToggled(element)
{
    // Relative selects
    if(element.value == "option5" && element.checked)
    {
        $("#option-show-int-lumi").prop("checked", false)
        $("#option-show-datetime").prop("checked", false)
    }
    else if(element.value == "option6" && element.checked)
    {
        $("#option-show-xrange").prop("checked", false)
        $("#option-show-datetime").prop("checked", false)
    }
    else if(element.value == "option7" && element.checked)
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
}

$(document).ready(function()
{
    readCheckboxOptionValues()
})
