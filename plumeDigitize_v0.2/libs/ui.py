#------------------------------------------------------------------------------------------------
# digitized tool created by Jiangping He
#------------------------------------------------------------------------------------------------

import os, json, webbrowser

class Digitizer:
    tmpl ="""
var geojson_output = '%s',
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
    });\n"""
    def __init__(self, layers):
        self.htmlroot = layers.pop('htmlroot')
        self.output = layers.pop('output')
        self.layer_groups = layers
    def open(self, html_file='digitizeIt.html'):
        html_file = '/'.join([self.htmlroot, html_file])
        t = Digitizer.tmpl%(self.output, json.dumps(self.layer_groups['overlayers']['firepixels']))
        for group in ['baselayers', 'overlayers']:
            laystr = []
            for name, layer in self.layer_groups[group].items():
                if name == 'firepixels':
                    laystr.append('  "firepixels": firepixelsLayer')
                else:
                    bbox = json.dumps([p[::-1] for p in layer['bbox_lonlat']])
                    laystr.append('  "{name}": L.imageOverlay("{path}", {bbox})'.format(name=name, path=layer['filename'], bbox=bbox))
            t += 'var {group}_dynamic = {{\n{layers}\n}};\n'.format(group=group, layers=',\n'.join(laystr))
        plum_geojson = '/'.join([self.htmlroot, self.output])
        plums = 'null'
        if os.path.exists(plum_geojson):
            with open(plum_geojson,'r') as f:
                plums = f.read()
        with open('/'.join([self.htmlroot, 'mylayers.js']), 'w') as f:
            f.write(t + 'var plums = ' + plums + ';\n')
        with open('libs/index.template.html','r') as f:
            message = f.read()
        with open(html_file,'w') as f:
            f.write(message)
        webbrowser.open_new_tab('file:///'+os.getcwd()+'/' + html_file)
