%chk=neonCISDTZVP.chk
%mem=2GB
%NProcShared=1
#P SP CISD/TZVP density=rhoci gfinput fchk=all out=wfx iop(9/40=7) iop(9/28=-1) use=l916

neonCISDTZVP neon CISD TZVP

0 1
Ne 0.0 0.0 0.0

neonCISDTZVP.wfx

