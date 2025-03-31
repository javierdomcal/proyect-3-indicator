%chk=CALC_000001.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/cc-pVQZ gfinput fchk=all density=current iop(5/33=1) out=wfx

CALC_000001 helium CASSCF(2,2) cc-pVQZ

0 1
He    0.0000   0.0000   0.0000

CALC_000001.wfx

