%chk=CALC_000057.chk
%mem=4GB
%NProcShared=1
#P SP CISD/cc-pVDZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000057 neon CISD cc-pVDZ

0 1
Ne 0.0 0.0 0.0

CALC_000057.wfx

