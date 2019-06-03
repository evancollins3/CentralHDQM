
function filterSelectionChanged()
{
    var value = $("#filter-select").val()
    var container = $("#filter-value-container")

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
}

async function getFilteredArray(data)
{
    var filter = $("#filter-select").val()

    if(filter == "latest")
    {
        var value = $("#filter-input-latest").val()
        return data.slice(-value)
    }
    else if(filter == "range")
    {
        var low = $("#filter-input-range-low").val()
        var high = $("#filter-input-range-high").val()

        return data.filter(x => x.run >= low && x.run <= high)
    }
    else if(filter == "list")
    {
        var value = $("#filter-input-list").val()
        value = value.replace(/\s/g, '')
        var runs = value.split(",").map(x => parseInt(x))

        return data.filter(x => runs.includes(x.run))
    }
    else if(filter == "json")
    {
        const file = $("#filter-input-file")[0].files[0]
        if(file == undefined)
            return []

        try
        {
            const fileContents = await readUploadedFileAsText(file)  
            var goldenJson = JSON.parse(fileContents)
            var runs = Object.keys(goldenJson).map(x => parseInt(x))
            
            return data.filter(x => runs.includes(x.run))
        }
        catch (e)
        {
            console.log("Unable to read golden json input file")
            return []
        }
    }
    else if(filter == "rr")
    {
        // To be implemented once API allows this
        return []
    }
}

function getFilterValue()
{
    var value = $("#filter-select").val()

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
}

function setFilterValue(filterValue)
{
    var value = $("#filter-select").val()

    if(value == "latest")
    {
        $("#filter-input-latest").val(filterValue)
    }
    else if(value == "range")
    {
        var highLow = filterValue.split(",")
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
}

$(document).ready(function()
{
    // Interpret url variables
    var filter = getUrlVariable("filter")
    if(filter != null)
        $("#filter-select").val(filter)
    
    filterSelectionChanged()

    var filterValue = getUrlVariable("filterValue")
    if(filter != null && filterValue != null)
        setFilterValue(getUrlVariable("filterValue"))

    $("#search-query-input").val(getUrlVariable("search"))
})
