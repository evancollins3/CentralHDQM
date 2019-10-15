
function addUrlVariable(name, value)
{
    // Remove all trailing slashes
    var href = location.href.replace(/\/+$/, "")
    var url = new URL(href)
    url.searchParams.delete(name)
    url.searchParams.append(name, value)
    
    history.pushState(undefined, "", url.toString())
}

function getUrlVariable(name)
{
    // Remove all trailing slashes
    var href = location.href.replace(/\/+$/, "")
    var url = new URL(href)

    var value = url.searchParams.get(name)
    return value != null ? value.replace(/\/+$/, "") : null
}

function hasUrlVariable(name)
{
    // Remove all trailing slashes
    var href = location.href.replace(/\/+$/, "")
    var url = new URL(href)
    return url.searchParams.has(name)
}

function deleteUrlVariable(name)
{
    // Remove all trailing slashes
    var href = location.href.replace(/\/+$/, "")
    var url = new URL(href)
    url.searchParams.delete(name)
    
    history.pushState(undefined, "", url.toString())
}
