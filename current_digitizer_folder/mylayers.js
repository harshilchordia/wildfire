
    var rgbLayer = L.imageOverlay('VIIRS_2019_12_20_T_0342.png', [[-37.80073165893555, 132.3426971435547], [-12.807840347290039, 168.5931701660156]]),
    emissionLayer = L.imageOverlay('s5p_2019_12_20_T_0259.png', [[-43.67700000000001, 112.953], [-9.177000000000007, 159.04500000000002]]),
    firepixels = {"type": "FeatureCollection", "features": []},
    firepixelsLayer = L.geoJson(firepixels, {
        pointToLayer: function (feature, latlng) {
            return L.circleMarker(latlng, {
                radius: 4,
                color: '#ff0000',
                weight: 1,
                fillColor: '#ffff00',
                fillOpacity: 1.0
            });
        }
    });