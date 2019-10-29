
const helpers = (function(){
    return {
        seriesColors: ["#7cb5ec", "#434348", "#90ed7d", "#f7a35c", "#8085e9", "#f15c80", "#e4d354", "#2b908f", "#f45b5b", "#91e8e1"],

        calculateMeanAndRMS: function(yValues)
        {
            // Concatenate all series
            var values = yValues.reduce((all, cur) => all.concat(cur), [])

            // Filter out all zeros
            values = values.filter(x => x != 0)

            if(values.length == 0)
                return [0, 0]

            var yValuesSum = values.reduce((total, num) => total + num, 0)
            var mean = yValuesSum / values.length

            var yValuesSquareSum = values.reduce((total, num) => total + (num * num), 0)
            var meanOfSquares = yValuesSquareSum / values.length

            var rms = Math.sqrt(meanOfSquares - (mean * mean))

            return [mean, rms]
        },

        getYRange: function(mean, rms)
        {
            var min_y = mean - (5 * rms)
            var max_y = mean + (5 * rms)

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
            var avg_y = 0, avg_x = 0
            var start_x = Infinity, end_x = 0
            var start_y = Infinity, end_y = 0

            for (var i = 0; i < data.length; i++) 
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

            var cov_xy = 0
            var var_x = 0
            var var_y = 0

            for (var i = 0; i < data.length; i++) 
            {
                cov_xy += (data[i].x - avg_x) * (data[i].y - avg_y)
                var_x += Math.pow(data[i].x - avg_x, 2)
                var_y += Math.pow(data[i].y - avg_y, 2)
            }

            var a_x = cov_xy / var_x
            var b_x = avg_y - a_x * avg_x
            var res = [[start_x, a_x * start_x + b_x], [end_x, a_x * end_x + b_x]]
            
            return res;
        },

        // Returns a color based on val which must be between 0.0 and 1.0
        colorScale: function(val) 
        {
            var r, g, b = 0
            var perc = 100 - val * 100

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
        }        
    }
}())
