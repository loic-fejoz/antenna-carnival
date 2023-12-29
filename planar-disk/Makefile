all: run

run:
	python3 Planar_Disk_Antenna.py

planar_disk_antenna.xml: Planar_Disk_Antenna.py
	POST_PROC_ONLY=True python3 Planar_Disk_Antenna.py

view: planar_disk_antenna.xml
	AppCSXCAD planar_disk_antenna.xml

.PHONY: view