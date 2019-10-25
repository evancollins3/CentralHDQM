
const displayConfig = (function() {
    const displayGroups = [
        { 
            name: "SomeNameLikeID",
            plot_title: "Fancy plot name 1",
            y_title: "Some title",
            subsystem: "Tracker",
            correlation: false,
            series: ["NumberOfALCARecoTracks", "NumberOfTrack_mean", "NumberofPVertices_mean"]
        },
        { 
            name: "SomeNameLikeID2",
            plot_title: "Fancy plot name 2",
            y_title: "Some title",
            subsystem: "Tracker",
            correlation: true,
            series: ["NumberOfTrack_mean", "NumberofPVertices_mean"]
        },
    ]
    
    return {
        displayGroups: displayGroups
    }
}())
