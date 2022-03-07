
    var rgbLayer = L.imageOverlay('tonga_goes.png', [[-12.404, 176.838], [-25.15, 192.92]]),
    emissionLayer = L.imageOverlay('MODIS_AOD-fake.png', [[-7.93, 169.55], [-33.93, 190.86]]),
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