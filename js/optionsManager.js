
var globalOptions = 
{
    showErrors: false,
    showFills: true,
    showDurations: true,
    showRegression: true,
    showXRange: false,
    showIntLumi: false,
    showDatetime: false,
    searchQuery: "",
}

function readOptionValues()
{
    globalOptions.showErrors = $("#option-show-errors").prop("checked")
    globalOptions.showFills = $("#option-show-fills").prop("checked")
    globalOptions.showDurations = $("#option-show-run-duration").prop("checked")
    globalOptions.showRegression = $("#option-show-regression-lines").prop("checked")
    globalOptions.showXRange = $("#option-show-xrange").prop("checked")
    globalOptions.showIntLumi = $("#option-show-int-lumi").prop("checked")
    globalOptions.showDatetime = $("#option-show-datetime").prop("checked")
    globalOptions.searchQuery = $("#search-query-input").val()
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

function updateOptionsUI()
{
    $("#option-show-errors").prop("checked", globalOptions.showErrors)
    $("#option-show-fills").prop("checked", globalOptions.showFills)
    $("#option-show-run-duration").prop("checked", globalOptions.showDurations)
    $("#option-show-regression-lines").prop("checked", globalOptions.showRegression)
    $("#option-show-xrange").prop("checked", globalOptions.showXRange)
    $("#option-show-int-lumi").prop("checked", globalOptions.showIntLumi)
    $("#option-show-datetime").prop("checked", globalOptions.showDatetime)

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

function getBitwiseSum()
{
    var showErrors = globalOptions.showErrors = $("#option-show-errors").prop("checked") << 0
    var showFills = globalOptions.showFills = $("#option-show-fills").prop("checked") << 1
    var showDurations = globalOptions.showDurations = $("#option-show-run-duration").prop("checked") << 2
    var showRegression = globalOptions.showRegression = $("#option-show-regression-lines").prop("checked") << 3
    var showXRange = globalOptions.showXRange = $("#option-show-xrange").prop("checked") << 4
    var showIntLumi = globalOptions.showIntLumi = $("#option-show-int-lumi").prop("checked") << 5
    var showDatetime = globalOptions.showDatetime = $("#option-show-datetime").prop("checked") << 6

    return showErrors + showFills + showDurations + showRegression + showXRange + showIntLumi + showDatetime
}

function setFromBitwiseSum(sum)
{
    globalOptions.showErrors = isBitSet(sum, 0)
    globalOptions.showFills = isBitSet(sum, 1)
    globalOptions.showDurations = isBitSet(sum, 2)
    globalOptions.showRegression = isBitSet(sum, 3)
    globalOptions.showXRange = isBitSet(sum, 4)
    globalOptions.showIntLumi = isBitSet(sum, 5)
    globalOptions.showDatetime = isBitSet(sum, 6)
}

function isBitSet(value, bit)
{
    var mask = 1 << bit
    return (value & mask) != 0
}

$(document).ready(function()
{
    if(hasUrlVariable("options"))
    {
        var optionsBitSum = getUrlVariable("options")
        setFromBitwiseSum(optionsBitSum)
        updateOptionsUI()
    }
})
