%chk=heliumcasscf22631g.chk
%mem=2GB
%NProcShared=1
#P SP CISD/6-31G density=rhoci gfinput fchk=all out=wfx iop(9/40=7) iop(9/28=-1) use=l916

helium CISD Calculation helium CISD 6-31G

0 1
He    0.0000   0.0000   0.0000

heliumcasscf22631g.wfx

