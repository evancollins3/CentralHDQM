
var dataIndex
var currentlySelectedTitles = []

function setupSelects()
{
    values = []
    
    var current = dataIndex['content']
    var categories = []

    while(true)
    {
        var currentTitle = getSelectTitleById(categories.length)
        var index = current.findIndex(x => Object.keys(x)[0] == currentTitle)
        if(index == -1)
            index = 0
        
        if(typeof current[index] != "string")
        {
            var optionsList = []
            current.forEach(option => 
            {
                if(typeof option != "string")
                    optionsList.push(Object.keys(option)[0])
            })
            categories.push(optionsList)
        }
        else
        {
            break
        }

        if(current.length == 0)
            break

        current = current[index][Object.keys(current[index])[0]]
    }

    updateSelects(categories)
}

function updateSelects(categories)
{
    var html = ""
    var count = 0

    categories.forEach(category => 
    {
        html += `<div class="col-12 col-md mt-2 mt-md-0">
        <select class="form-control form-control-sm" id="select_category_${count}" onchange="selectChanged(this)">`

        category.forEach(item => {
            if(getSelectTitleById(count) == item)
            {
                html += `<option selected>` + item + `</option>`
            }
            else
            {
                html += `<option>` + item + `</option>`
            }
        })
        
        html += `</select></div>`
        count ++
    })

    $("#data-selection-container").html(html)
}

function getSelectTitleById(id)
{
    if(currentlySelectedTitles.length > id)
    {
        return currentlySelectedTitles[id]
    }

    return null
}

function setSelectTitleById(id, title)
{
    currentlySelectedTitles[id] = title
}

function selectChanged(select)
{
    var selectId = select.id.split("_")[2]
    setSelectTitleById(selectId, select.value)
    setupSelects()
}

function getFileListForCurrentSelection()
{
    var selects = $("#data-selection-container").find("select")
    var list = selects.map(i => selects[i].value).toArray()

    var current = dataIndex['content']
    list.forEach(dir => 
    {
        current = current.find(x => Object.keys(x)[0] == dir)[dir]
    })

    // If files appear only as components of other plots, don't show them separately
    var files = []
    current.forEach(file => 
    {
        file = file.split(".")[0]
        var existsAsTopLevel = collections.filter(x => x["name"] == file).length != 0

        if(existsAsTopLevel)
            files.push(file)
    })

    return files.map(x => "./data/alljsons/" + list.join("/") + "/" + x)
}

function getJustFilename(fullPath)
{
    var parts = fullPath.split("/")
    var nameWithExt = parts[parts.length - 1]
    return nameWithExt.split(".")[0]
}

function getJustDirname(fullPath)
{
    var parts = fullPath.split("/")
    parts.pop()
    return parts.join("/") + "/"
}

function traverseTillEnd(current, list)
{
    if(typeof current[index] == "string")
    {
        return current
    }
    else
    {
        var currentTitle = list[0]
        var index = current.findIndex(x => Object.keys(x)[0] == currentTitle)
        current = current[index][Object.keys(current[index])[0]]
        return traverseTillEnd(current, list.slice(1))
    }
}

$(document).ready(async function() 
{
    const response = await fetch("./data/index.json")
    dataIndex = await response.json()

    currentlySelectedTitles[0] = "2018"
    currentlySelectedTitles[1] = "StreamExpress"
    currentlySelectedTitles[2] = "PixelPhase1"
    setupSelects()
})
