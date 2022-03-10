from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure(figsize=(12,9))

m = Basemap(projection='mill',
           llcrnrlat = -90,
           urcrnrlat = 90,
           llcrnrlon = -180,
           urcrnrlon = 180,
           resolution = 'c')

m.drawcoastlines()
m.drawcountries(color='red')
m.drawstates(color='blue')
m.drawcounties(color='orange')
m.drawrivers(color='blue')

m.drawmapboundary(color='pink', linewidth=10, fill_color='aqua')
m.fillcontinents(color='lightgreen', lake_color='aqua')

m.drawlsmask(land_color='lightgreen', ocean_color='aqua', lakes=True)

m.etopo()
m.bluemarble()
m.shadedrelief()

m.drawparallels(np.arange(-90,90,10),labels=[True,False,False,False])
m.drawmeridians(np.arange(-180,180,30),labels=[0,0,0,1])

np.arange(start,stop,step)
labels=[left,right,top,bottom]

plt.title('Basemap tutorial', fontsize=20)

plt.show()