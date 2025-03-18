window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng, context) {
            const {
                circleOptions
            } = context.hideout;
            return L.circleMarker(latlng, circleOptions); // render a simple circle marker
        }
    }
});