%chk=CALC_000006.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/aug-cc-pVDZ gfinput fchk=all density=current iop(5/33=1) out=wfx

CALC_000006 helium CASSCF(2,2) aug-cc-pVDZ

0 1
He    0.0000   0.0000   0.0000

CALC_000006.wfx

