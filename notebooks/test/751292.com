%chk=751292.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/cc-pVDZ gfinput fchk=all density=current iop(5/33=1) out=wfx

751292 helium CASSCF(2,2) cc-pVDZ

0 1
He    0.0000   0.0000   0.0000

751292.wfx

