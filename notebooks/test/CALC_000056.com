%chk=CALC_000056.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(10,10)/cc-pVQZ gfinput fchk=all density=current iop(5/33=1) iop(4/21=100) out=wfx

CALC_000056 neon CASSCF(10,10) cc-pVQZ

0 1
Ne 0.0 0.0 0.0

CALC_000056.wfx

