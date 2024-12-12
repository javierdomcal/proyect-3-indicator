%chk=heliumCISDTZVP.chk
%mem=2GB
%NProcShared=1
#P SP CISD/TZVP density=rhoci gfinput fchk=all out=wfx iop(9/40=7) iop(9/28=-1) use=l916

heliumCISDTZVP helium CISD TZVP

0 1
He    0.0000   0.0000   0.0000

heliumCISDTZVP.wfx

