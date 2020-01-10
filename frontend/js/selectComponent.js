
const selectComponent = (function() {
    return {
        dataIndex: {},
        selects: {},
        placeholders: {},

        register: function(selects, data, placeholders = undefined)
        {
            const id = selects.join('_')

            this.dataIndex[id] = data
            this.selects[id] = selects
            this.placeholders[id] = placeholders

            selects.forEach((select, i) => {
                $(select).off('change')
                $(select).change(function() {
                    selectComponent.onChange(id, select)
                })
                
            })

            this.fillData(id, selects[0])
        },

        onChange: function(id, select) {
            const index = this.selects[id].indexOf(select) + 1
            const next = this.selects[id][index]

            if(next === undefined)
                return
            
            this.fillData(id, next)
        },

        fillData: function(id, select) {
            const index = this.selects[id].indexOf(select)
            $(select).empty()

            if(this.placeholders[id] !== undefined && this.placeholders[id][index] !== undefined)
            {
                const placeholder = document.createElement("option")
                placeholder.text = this.placeholders[id][index]
                placeholder.disabled = true
                placeholder.selected = true
                $(select).append(placeholder)
            }

            let data = this.dataIndex[id]

            for(let i = 0; i < index; i++) 
            {
                const val = $(this.selects[id][i]).val()
                if(data !== undefined)
                    data = data[val]
            }

            if(data !== undefined && !Array.isArray(data))
            {
                // Not the last level yet
                data = Object.keys(data)
                data.forEach(element => 
                {
                    const option = document.createElement("option")
                    option.text = element
                    $(select).append(option)
                })
            }
            else if(data !== undefined)
            {
                // Last level already
                data.forEach(element => 
                {
                    const option = document.createElement("option")

                    if(element['id'] !== undefined)
                    {
                        option.text = element['name']
                        option.value = element['id']
                    }
                    else
                    {
                        option.text = element
                    }

                    $(select).append(option)
                })
            }

            $(select).trigger("change")
        },
    }
}())
