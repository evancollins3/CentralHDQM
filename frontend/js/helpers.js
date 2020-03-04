
const helpers = (function(){
    return {
        seriesColors: ["#7cb5ec", "#434348", "#90ed7d", "#f7a35c", "#8085e9", "#f15c80", "#e4d354", "#2b908f", "#f45b5b", "#91e8e1"],

        calculateMeanAndRMS: function(yValues)
        {
            // Concatenate all series
            let values = yValues.reduce((all, cur) => all.concat(cur), [])

            // Filter out all zeros
            values = values.filter(x => x != 0)

            if(values.length == 0)
                return [0, 0]

            let yValuesSum = values.reduce((total, num) => total + num, 0)
            let mean = yValuesSum / values.length

            let yValuesSquareSum = values.reduce((total, num) => total + (num * num), 0)
            let meanOfSquares = yValuesSquareSum / values.length

            let rms = Math.sqrt(meanOfSquares - (mean * mean))

            return [mean, rms]
        },

        getYRange: function(mean, rms)
        {
            let min_y = mean - (5 * rms)
            let max_y = mean + (5 * rms)

            return [min_y, max_y]
        },

        safeGetAtIndex: function(array, index)
        {
            if(array != undefined)
                return array[index]
            else
            {
                return undefined
            }
        },

        linearRegression: function(data) 
        {
            let avg_y = 0, avg_x = 0
            let start_x = Infinity, end_x = 0
            let start_y = Infinity, end_y = 0

            for (let i = 0; i < data.length; i++) 
            {
                avg_y += data[i].y
                avg_x += data[i].x
                if (start_x > data[i].x)
                    start_x = data[i].x
                if (end_x < data[i].x) 
                    end_x = data[i].x
                if (start_y > data[i].y)
                    start_y = data[i].y
                if (end_y < data[i].y) 
                    end_y = data[i].y
            }

            start_x -= Math.abs(start_x)
            end_x += Math.abs(end_x)
            start_y -= Math.abs(start_y)
            end_y += Math.abs(end_y)
            avg_x /= data.length
            avg_y /= data.length

            let cov_xy = 0
            let var_x = 0
            let var_y = 0

            for (let i = 0; i < data.length; i++) 
            {
                cov_xy += (data[i].x - avg_x) * (data[i].y - avg_y)
                var_x += Math.pow(data[i].x - avg_x, 2)
                var_y += Math.pow(data[i].y - avg_y, 2)
            }

            let a_x = cov_xy / var_x
            let b_x = avg_y - a_x * avg_x
            let res = [[start_x, a_x * start_x + b_x], [end_x, a_x * end_x + b_x]]
            
            return res;
        },

        // Returns a color based on val which must be between 0.0 and 1.0
        colorScale: function(val)
        {
            let r, g, b = 0
            const perc = 100 - val * 100

            if(perc < 50) 
            {
                r = 255;
                g = Math.round(5.1 * perc)
            }
            else 
            {
                g = 255
                r = Math.round(510 - 5.10 * perc)
            }
            
            var h = r * 0x10000 + g * 0x100 + b * 0x1
            return '#' + ('000000' + h.toString(16)).slice(-6)
        },

        secondsToHHMMSS: function(total) {
            let hours = 0
            let minutes = 0
            let seconds = 0

            hours = Math.floor(total / 3600)
            minutes = Math.floor((total % 3600) / 60)
            seconds = (total % 3600) % 60

            if(String(hours).length == 1)
                hours = "0" + hours

            if(String(minutes).length == 1)
                minutes = "0" + minutes

            if(String(seconds).length == 1)
                seconds = "0" + seconds

            return hours + ":" + minutes + ":" + seconds
        }
    }
}())
