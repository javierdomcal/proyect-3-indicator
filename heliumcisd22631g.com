%chk=heliumcisd22631g.chk
%mem=2GB
%NProcShared=test/heliumcisd22631g.com
#P SP CISD/6-31G density=rhoci gfinput fchk=all out=wfx iop(9/40=7) iop(9/28=-1) use=l916

heliumcisd22631g helium CISD 6-31G

0 1
He    0.0000   0.0000   0.0000

heliumcisd22631g.wfx

