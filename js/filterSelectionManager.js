
function filterSelectionChanged()
{
    var value = $("#filter-select").val()
    var marker = $("#filter-value-marker")
    
    // Remove previous item
    marker.nextAll().remove()

    if(value == "latest")
    {
        $(`<div class="col-12 col-md-6 mt-2 mt-md-0">
            <input type="number" class="form-control form-control-sm" id="filter-input-latest" value="50" placeholder="Number of latest runs">
        </div>`).insertAfter(marker)
    }
    else if(value == "range")
    {
        $(`<div class="col-6 col-md-3 mt-2 mt-md-0">
        <input type="number" class="form-control form-control-sm" id="filter-input-range-low" value="322348" placeholder="From">
        </div>
        <div class="col-6 col-md-3 mt-2 mt-md-0">
            <input type="number" class="form-control form-control-sm" id="filter-input-range-high" value="325310" placeholder="To">
        </div>`).insertAfter(marker)
    }
    else if(value == "list")
    {
        $(`<div class="col-12 col-md-6 mt-2 mt-md-0">
            <input type="text" class="form-control form-control-sm" id="filter-input-list" value="325308, 325309, 325310" placeholder="Comma separated list of run numbers">
        </div>`).insertAfter(marker)
    }
    else if(value == "json")
    {
        $(`<div class="col-12 col-md-6 mt-2 mt-md-0">
            <input type="file" class="form-control form-control-sm form-control-file" id="filter-input-file" style="padding-top: 2px;">
        </div>`).insertAfter(marker)
    }
    else if(value == "rr")
    {
        $(`<div class="col-12 col-md-6 mt-2 mt-md-0">
            <input type="text" class="form-control form-control-sm" placeholder="https://cmsrunregistry.web.cern.ch/online/runs/all">
        </div>`).insertAfter(marker)
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
        const file = document.getElementById("filter-input-file").files[0]
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

$(document).ready(function()
{
    filterSelectionChanged()
})
