
    var rgbLayer = L.imageOverlay('VIIRS_2019_12_01_T_0436.png', [[-43.73729562697552, 112.92258245849632], [-9.14736093363615, 159.0987229003909]]),
    emissionLayer = L.imageOverlay('s5p_png_2019_12_01_T_0357.png', [[-43.73729562697552, 112.92258245849632], [-9.14736093363615, 159.0987229003909]]),
    firepixels = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [176.838, -12.404]}}, {"type": "Feature", "geometry": {"type": "Point", "coordinates": [180, -21]}}, {"type": "Feature", "geometry": {"type": "Point", "coordinates": [192.92, -25.15]}}]},
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