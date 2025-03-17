%chk=CALC_000039.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(4,5)/aug-cc-pVQZ gfinput fchk=all density=current iop(5/33=1) out=wfx

CALC_000039 berilium CASSCF(4,5) aug-cc-pVQZ

0 1
Be    0.0000   0.0000   0.0000

CALC_000039.wfx

