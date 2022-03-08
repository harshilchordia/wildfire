
    var rgbLayer = L.imageOverlay('VIIRS_2019_12_20_T_0336.png', [[-58.524696350097656, -179.99990844726562], [-32.62281799316407, 179.99990844726562]]),
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