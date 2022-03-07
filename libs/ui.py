import os, json, webbrowser

class Digitizer:
    tmpl ="""
    var rgbLayer = L.imageOverlay('%s', %s),
    emissionLayer = L.imageOverlay('%s', %s),
    firepixels = %s,
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
    });"""
    def __init__(self, layers):
        layers['rgb']['path'] = layers['rgb']['filename']
        layers['emission']['path'] = layers['emission']['filename']
        self.htmlroot = layers['htmlroot']
        self.layers = layers
    def open(self, html_file='digitizeIt.html'):
        html_file = '/'.join([self.htmlroot, html_file])
        t = Digitizer.tmpl%(self.layers['rgb']['path'],
            json.dumps([p[::-1] for p in self.layers['rgb']['bbox_lonlat']]),
            self.layers['emission']['path'],
            json.dumps([p[::-1] for p in self.layers['emission']['bbox_lonlat']]),
            json.dumps(self.layers['firepixels']))
        with open('/'.join([self.layers['htmlroot'], 'mylayers.js']), 'w') as f:
            f.write(t)
        with open('libs/index.template.html','r') as f:
            message = f.read()
        with open(html_file,'w') as f:
            f.write(message)
        webbrowser.open_new_tab('file:///'+os.getcwd()+'/' + html_file)