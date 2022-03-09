import rasterio
from rasterio.plot import show
from rasterio.windows import Window
import numpy as np
import csv
from osgeo import gdal
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from pyproj import Proj, transform
import webbrowser
from flask import Flask, render_template, request, Markup


webbrowser.open_new_tab('http://localhost:5000/') #Start html GUI

def house(address, window_type):
	if window_type == "house":
		offset = 70
	else:
		offset = 200
	#http://loc.geopunt.be/geolocation/location?q=kantersteen,brussel,10
	geolocator = Nominatim(user_agent="3D-houses2")
	location = geolocator.geocode(address)
	x1,y1 = location.latitude, location.longitude
	inputEPSG = Proj('epsg:4326')
	outputEPSG = Proj('epsg:31370')
	x2,y2 = transform(inputEPSG,outputEPSG,x1,y1)

	for i in range(1, 44):
		with rasterio.open(f"data/DHMVIIDSMRAS1m_k{i:02d}/GeoTIFF/DHMVIIDSMRAS1m_k{i:02d}.tif") as f:
			if (f.bounds[0] < x2 < f.bounds[2]) and (f.bounds[1] < y2 < f.bounds[3]):
				print(f"found in DHMVIIDSMRAS1m_k{i:02d}")
				tif_file = i
				break
	else:
		print("Not found")

	with rasterio.open(f"data/DHMVIIDSMRAS1m_k{tif_file:02d}/GeoTIFF/DHMVIIDSMRAS1m_k{tif_file:02d}.tif") as src:
		x,y = src.index(x2, y2)
		w = src.read(1, window=Window(y-(offset/2), x-(offset/2), offset, offset))

	X = np.arange(0, w.shape[0]*1, 1)
	Y = np.arange(0, w.shape[1]*-1, -1)
	X, Y = np.meshgrid(X, Y)


	fig = go.Figure(data=[go.Surface(z=w, x=X, y=Y)])
	fig.update_layout(title=address.title(), autosize=False,
	                  width=1300, height=600,
	                  margin=dict(l=65, r=50, b=65, t=90))
	
	scene=dict(camera=dict(eye=dict(x=1.15, y=1.15, z=0.8)), #the default values are 1.25, 1.25, 1.25
	           xaxis=dict(visible=False, showgrid=False),
	           yaxis=dict(visible=False, showgrid=False),
	           zaxis=dict(visible=False, showgrid=False),
	           aspectmode='data', #this string can be 'data', 'cube', 'auto', 'manual'
	           #a custom aspectratio is defined as follows:
	           #aspectratio=dict(x=1, y=1, z=1/2)
	           )
	fig.update_layout(scene=scene)

	fig.update_traces(showscale=False)
	fig.show()

app = Flask(__name__, static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def address():
	if request.form.get('text', '') != "":
		house(request.form.get('text',''), request.form.get('window'))
	return render_template('app.html')

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000)