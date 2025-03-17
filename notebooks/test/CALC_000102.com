%chk=CALC_000102.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/aug-cc-pVQZ gfinput fchk=all density=current iop(5/33=1) out=wfx

CALC_000102 hydrogen_2eq CASSCF(2,2) aug-cc-pVQZ

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

CALC_000102.wfx

