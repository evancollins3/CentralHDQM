
const helpers = (function(){
    return {
        seriesColors: ["#f45b5b", "#7cb5ec", "#f7a35c", "#2b908f", "#e4d354", "#91e8e1", "#8085e9", "#434348", "#90ed7d", "#f15c80"],

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

            // Derive an equation of a line when you know 2 point it passes through (y=mx+b):
            let m = (res[1][1] - res[0][1]) / (res[1][0] - res[0][0])
            let b = res[0][1] - (m * res[0][0])

            m = parseFloat(m.toFixed(2))
            b = parseFloat(b.toFixed(2))

            const sign = b > 0 ? "+" : "-"
            b = Math.abs(b)

            let equation = `y = ${m}x ${sign} ${b}`

            if(b === 0 && m === 0)
                equation = `y = x`
            else if(b === 0)
                equation = `y = ${m}x`
            else if(m === 0)
                equation = `y = ${b}`
            
            return [res, equation]
        },

        multipleRegression3D: function(data) 
        {
            // Least squares method
            const A = [
                [data.reduce((a, n) => a + n.x * n.x, 0), data.reduce((a, n) => a + n.x * n.y, 0), data.reduce((a, n) => a + n.x, 0)],
                [data.reduce((a, n) => a + n.x * n.y, 0), data.reduce((a, n) => a + n.y * n.y, 0), data.reduce((a, n) => a + n.y, 0)],
                [data.reduce((a, n) => a + n.x, 0), data.reduce((a, n) => a + n.y, 0), data.length]
            ]

            const b = [data.reduce((a, n) => a + n.x * n.z, 0), data.reduce((a, n) => a + n.y * n.z, 0), data.reduce((a, n) => a + n.z, 0)]

            // math.js has to be imported for this to work
            const x = math.usolve(A, b)

            // x now holds the coefficients of the 3d equation
            console.log(x)

            let equation = "a + b + c"
            return [res, equation]
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
        },

        toExponential: function(num, x) {
            if(num === null || num === undefined) {
                return undefined
            }
            
            if(x === undefined) {
                return num.toExponential()
            }
            else {
                return num.toExponential(x)
            }
        }
    }
}())
