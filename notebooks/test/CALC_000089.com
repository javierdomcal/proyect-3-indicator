%chk=CALC_000089.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/cc-pVQZ gfinput fchk=all density=current iop(5/33=1) out=wfx

CALC_000089 hydrogen CASSCF(2,2) cc-pVQZ

0 1
H    0.000000   0.000000  -0.370000
H    0.000000   0.000000   0.370000

CALC_000089.wfx

