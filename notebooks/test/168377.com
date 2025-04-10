%chk=168377.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(4,5)/cc-pVDZ gfinput fchk=all density=current iop(5/33=1) out=wfx

168377 beryllium CASSCF(4,5) cc-pVDZ

0 1
