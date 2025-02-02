# -*- coding: utf-8 -*-
"""
 J-antenna for 868MHz meshtastic
 based on Simple Patch Antenna Tutorial
"""

### Import Libraries
import os, tempfile
from pylab import *

from CSXCAD  import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import *

### General parameter setup
Sim_Path = os.path.join(tempfile.gettempdir(), 'j-meshtastic')

post_proc_only = False

scotch_width=10 #mm
scotch_thickness=0.1 #mm

#substrate setup
substrate_epsR   = 2.1 # relative permittivity (void=1, PTFE=2.1, PVC=3.3, FR4=4.4, ...)
substrate_kappa  = 1e-3 * 2*pi*2.45e9 * EPS0*substrate_epsR
substrate_thickness = 1.524
substrate_cells = 4

copper_conductivity = 5.96e7
aluminium_conductivity = 3.77e7

#setup feeding
feed_pos = 8.0 #feeding position in y-direction
feed_R = 50     #feed resistance

# setup FDTD parameter & excitation function
f0 = 868e6 # center frequency
fc = 200e6

### FDTD setup
## * Limit the simulation to NrTS timesteps
## * Define a reduced end criteria of -40dB
FDTD = openEMS(NrTS=85000, EndCriteria=1e-4)
FDTD.SetGaussExcite( f0, fc )
FDTD.SetBoundaryCond( ['MUR', 'MUR', 'MUR', 'MUR', 'MUR', 'MUR'] )


CSX = ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(1e-3)
mesh_res = C0/(f0+fc)/1e-3/30

### Generate properties, primitives and mesh-grid
#initialize the mesh with the "air-box" dimensions
mesh.AddLine('x', [-200, 200])
mesh.AddLine('y', [-100, 400])
mesh.AddLine('z', [-50, 100])

# create patch
#patch = CSX.AddMetal( 'J') # create a perfect electric conductor (PEC)
patch = CSX.AddConductingSheet( 'J', conductivity=copper_conductivity)
patch.AddBox(priority=10, start=[-10, 10, substrate_thickness], stop=[ 0, 248.5, substrate_thickness+scotch_thickness])
patch.AddBox(priority=10, start=[  8, 10, substrate_thickness], stop=[18,  83.3, substrate_thickness+scotch_thickness])
patch.AddBox(priority=10, start=[-10, 0, substrate_thickness], stop=[18,  10, substrate_thickness+scotch_thickness])
FDTD.AddEdges2Grid(dirs='xy', properties=patch, metal_edge_res=mesh_res/2)

mesh.AddLine('x', linspace(-15, 23, 19))
mesh.AddLine('y', linspace(-5, 255, 131))

# create substrate
substrate = CSX.AddMaterial( 'substrate', epsilon=substrate_epsR, kappa=substrate_kappa)
start = [-20, -10, 0]
stop  = [ 28, 258.5, substrate_thickness]
substrate.AddBox( priority=0, start=start, stop=stop )

# add extra cells to discretize the substrate thickness
mesh.AddLine('z', linspace(0,substrate_thickness,substrate_cells+1))

# apply the excitation & resist as a current source
start = [0, 10 + feed_pos, substrate_thickness]
stop  = [10, 10 + feed_pos, substrate_thickness]
port = FDTD.AddLumpedPort(1, feed_R, start, stop, 'x', 1.0, priority=5, edges2grid='yz')

mesh.SmoothMeshLines('all', mesh_res, 1.4)

# Add the nf2ff recording box
nf2ff = FDTD.CreateNF2FFBox()

### Run the simulation
if True:  # debugging only
    CSX_file = os.path.join(Sim_Path, 'simp_patch.xml')
    if not os.path.exists(Sim_Path):
        os.mkdir(Sim_Path)
    CSX.Write2XML(CSX_file)
    print("File written into ", CSX_file)
    from CSXCAD import AppCSXCAD_BIN
    os.system(AppCSXCAD_BIN + ' "{}"'.format(CSX_file))

if not post_proc_only:
    FDTD.Run(Sim_Path, verbose=3, cleanup=False)


### Post-processing and plotting
f = np.linspace(max(1e3,f0-fc),f0+fc,401)
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
else:
    f_res = f[idx[0]]
    print('Resonance frequency: {} MHz'.format(f_res/1e6))
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

show()
