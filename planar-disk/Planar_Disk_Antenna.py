# -*- coding: utf-8 -*-
"""
 Planar Disk Antenna

 Tested with
  - python 3.8.10
  - openEMS v0.0.36

 (c) 2023 Loïc Fejoz <loic@fejoz.net>

"""

### Import Libraries
import sys
from mpl_smithchart import SmithAxes
import os, tempfile
from pylab import *

from CSXCAD  import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import *

### General parameter setup
Sim_Path = os.path.join(tempfile.gettempdir(), 'Planar_Disk')

post_proc_only = bool(os.getenv("POST_PROC_ONLY", False))

mm = 1e-3
cm = 1e-2
unit = mm # all length in mm

# disk radius
disk_radius = 70 * cm
disk_thickness = 3 * mm

# distance between the two disks
disk_sep = 1 * mm

#setup feeding
feed_R = 50     #feed resistance

# size of the simulation box
SimBox = np.array([4*disk_radius, 6*disk_radius, 2*disk_radius])
SimBox_center = np.array([0, 0, 0])

# setup FDTD parameter & excitation function
f0 = 435e6 # center frequency
lambda0 = round(C0/f0/unit) # wavelength in mm
fc = 100e6

### FDTD setup
## * Limit the simulation to NrTS timesteps
## * Define a reduced end criteria of -30dB
FDTD = openEMS(NrTS=40000000, EndCriteria=1e-3)
FDTD.SetGaussExcite(f0, fc)
FDTD.SetBoundaryCond( ['MUR', 'MUR', 'MUR', 'MUR', 'MUR', 'MUR'] )


CSX = ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(unit)
max_res = floor(C0 / (f0+fc) / unit / 10) # cell size: lambda/20

### Generate properties, primitives and mesh-grid
#initialize the mesh with the "air-box" dimensions
# mesh.AddLine('x', [-SimBox[0], SimBox[0]])
# mesh.AddLine('y', [-SimBox[1], SimBox[1]])
# mesh.AddLine('z', [-SimBox[2], SimBox[2]])
n=4
mesh.AddLine('x', np.linspace(-SimBox[0], SimBox[0], n))
mesh.AddLine('x', np.linspace(-disk_radius, disk_radius, n))
mesh.SmoothMeshLines('x', max_res, ratio=1.4)
mesh.AddLine('y', np.linspace(-SimBox[1], SimBox[1], n))
mesh.AddLine('y', np.linspace(-3*disk_radius-disk_sep, 3*disk_radius+disk_sep, 2*n))
mesh.AddLine('y', [-disk_sep, disk_sep])
mesh.SmoothMeshLines('y', max_res, ratio=1.4)
mesh.AddLine('z', np.linspace(-SimBox[2], SimBox[2], n))
mesh.AddLine('y', np.linspace(0, disk_thickness, n))
mesh.SmoothMeshLines('z', max_res, ratio=1.4)


# create disk 1
disk1 = CSX.AddMetal( 'disk1' ) # create a perfect electric conductor (PEC)
start = SimBox_center + [0, disk_radius + disk_sep/2, 0]
stop  = start + [0, 0, disk_thickness]
disk1.AddCylinder(start, stop, disk_radius)
FDTD.AddEdges2Grid(dirs='xy', properties=disk1, metal_edge_res=max_res/2)

# create disk 2
disk2 = CSX.AddMetal( 'disk2' ) # create a perfect electric conductor (PEC)
start = SimBox_center + [0, -disk_radius-disk_sep/2, 0]
stop  = start + [0, 0, disk_thickness]
disk2.AddCylinder(start, stop, disk_radius)
FDTD.AddEdges2Grid(dirs='xy', properties=disk2, metal_edge_res=max_res/2)

# add extra cells to discretize the disk thickness
# n = 5
# mesh.AddLine('z', linspace(-n*disk_thickness, n*disk_thickness, 6*n))
# mesh.SmoothMeshLines('z', max_res, 3)

# mesh.AddLine('x', linspace(-SimBox[0]/3, SimBox[0]/3, 10))
# mesh.AddLine('y', linspace(-SimBox[1]/3, SimBox[1]/3, 10))
# mesh.AddLine('z', linspace(-SimBox[2]/3, SimBox[2]/3, 10))
# mesh.SmoothMeshLines('all', max_res, 1.4)

# apply the excitation & resist as a current source
start = SimBox_center + [0, disk_sep/2, disk_thickness]
stop  = SimBox_center + [0, -disk_sep/2, disk_thickness]
port = FDTD.AddLumpedPort(1, feed_R, start, stop, 'y', 1.0, priority=5, edges2grid='xz')
# port = FDTD.AddLumpedPort(1, feed_R, start, stop, 'z', 1.0, priority=5)

CSX_file = 'planar_disk_antenna.xml'
CSX.Write2XML(CSX_file)

# Add the nf2ff recording box
# nf2ff = FDTD.CreateNF2FFBox()
nf2ff = FDTD.CreateNF2FFBox(opt_resolution=[lambda0/15]*3)

CSX.Write2XML(CSX_file)
# from CSXCAD import AppCSXCAD_BIN
# os.system(AppCSXCAD_BIN + ' "{}"'.format(CSX_file))
# import sys
# sys.exit(0)
### Run the simulation
if not post_proc_only:
    FDTD.Run(Sim_Path, verbose=3, cleanup=True)


### Post-processing and plotting
f = linspace(f0-fc, f0+fc, 401)
port.CalcPort(Sim_Path, f)
s11 = port.uf_ref/port.uf_inc
s11_dB = 20.0*np.log10(np.abs(s11))
figure()
plot(f/1e6, s11_dB, 'k-', linewidth=2, label='$S_{11}$')
grid()
legend()
ylabel('S-Parameter (dB)')
xlabel('Frequency (MHz)')

idx = np.where((s11_dB<-10) & (s11_dB==np.min(s11_dB)))[0]
if not len(idx)==1:
    print('No resonance frequency found for far-field calulation')
    # sys.exit(1)
else:
    f_res = f[idx[0]]
    theta = np.arange(-180.0, 180.0, 2.0)
    phi   = [0., 90.]
    nf2ff_res = nf2ff.CalcNF2FF(Sim_Path, f_res, theta, phi, center=[0,0,1e-3])

    figure()
    E_norm = 20.0*np.log10(nf2ff_res.E_norm[0]/np.max(nf2ff_res.E_norm[0])) + nf2ff_res.Dmax[0]
    plot(theta, np.squeeze(E_norm[:,0]), 'k-', linewidth=2, label='xz-plane')
    plot(theta, np.squeeze(E_norm[:,1]), 'r--', linewidth=2, label='yz-plane')
    grid()
    ylabel('Directivity (dBi)')
    xlabel('Theta (deg)')
    title('Frequency: {} MHz'.format(f_res/1e6))
    legend()

Zin = port.uf_tot/port.if_tot
figure()
plot(f/1e6, np.real(Zin), 'k-', linewidth=2, label='$\Re\{Z_{in}\}$')
plot(f/1e6, np.imag(Zin), 'r--', linewidth=2, label='$\Im\{Z_{in}\}$')
grid()
legend()
ylabel('Zin (Ohm)')
xlabel('Frequency (MHz)')

figure(figsize=(6, 6))

ax = subplot(1, 1, 1, projection='smith')
plot(Zin, label="default", datatype=SmithAxes.Z_PARAMETER)

show()
