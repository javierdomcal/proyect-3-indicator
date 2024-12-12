%chk=heliumCISD6-311G.chk
%mem=4GB
%NProcShared=1
#P SP CISD/6-311G gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

heliumCISD6-311G helium CISD 6-311G

0 1
He    0.0000   0.0000   0.0000

heliumCISD6-311G.wfx

