
const urlController = (function() {
    return {
        set: function(name, value)
        {
            // Remove all trailing slashes
            const href = location.href.replace(/\/+$/, "")
            const url = new URL(href)
            url.searchParams.delete(name)
            url.searchParams.append(name, value)
            
            history.pushState(undefined, "", url.toString())
        },

        get: function(name)
        {
            // Remove all trailing slashes
            const href = location.href.replace(/\/+$/, "")
            const url = new URL(href)

            const value = url.searchParams.get(name)
            return value != null ? value.replace(/\/+$/, "") : null
        },

        has: function(name)
        {
            // Remove all trailing slashes
            const href = location.href.replace(/\/+$/, "")
            const url = new URL(href)
            return url.searchParams.has(name)
        },

        delete: function(name)
        {
            // Remove all trailing slashes
            const href = location.href.replace(/\/+$/, "")
            const url = new URL(href)
            url.searchParams.delete(name)
            
            history.pushState(undefined, "", url.toString())
        }
    }
}())
